#!/usr/bin/env python3

# 1. Imports
# ==============================================================================
import sys
import re
import json
import argparse
import os
import traceback
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Union

# 1.1. Color Manipulation Import
# ------------------------------------------------------------------------------
try:
    import colorsys
except ImportError:
    colorsys = None # Allow script to run without it, but transformations will fail

# 1.2. Pygments Import (Optional)
# ------------------------------------------------------------------------------
try:
    import pygments
    from pygments.lexers import get_lexer_by_name
    from pygments.util import ClassNotFound
except ImportError:
    pygments = None; ClassNotFound = Exception; get_lexer_by_name = lambda *a, **k: (_ for _ in ()).throw(ClassNotFound()) # type: ignore

# 1.3. Rich Imports
# ------------------------------------------------------------------------------
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.syntax import Syntax
from rich.rule import Rule
from rich.style import Style, StyleType
# --- MODIFICATION: Import ColorTriplet too ---
from rich.color import Color, ColorType, ColorTriplet
# --- END MODIFICATION ---
from rich.errors import StyleSyntaxError
from rich.tree import Tree
from rich.measure import Measurement

# Type alias for style definitions in config
StyleDefinition = Union[str, Dict[str, Any]]

# ==============================================================================
# 2. Default Configuration Content
# ==============================================================================
# --- DETECTION RULES ---
DEFAULT_DETECTION_JSON = {
    "code_block_fence": r"^\s*```(\w*)", "blockquote_start": r"^\s*>",
    "header_numbered": r"^\*\*(\d+)\.\s+(.*?)\*\*$", "header1": r"^#\s+(.*)", "header2": r"^##\s+(.*)", "header3": r"^###\s+(.*)",
    "list_item_bullet": r"^(\s*)[-*+]\s+(.*)", "list_item_numbered": r"^(\s*)\d+\.\s+(.*)",
    "horizontal_rule": r"^\s*([-*_]){3,}\s*$", "key_value_colon": r"^\s*([\w\s-]+?)\s*:\s+(.*)",
    "inline_bold_star": r"(?P<bold_star>\*\*(?P<content_bold_star>.*?)\*\*)",
    "inline_bold_under": r"(?P<bold_under>__(?P<content_bold_under>.*?)__)",
    "inline_italic_star": r"(?P<italic_star>\*(?P<content_italic_star>.*?)\*)",
    "inline_italic_under": r"(?P<italic_under>_(?P<content_italic_under>.*?)_)",
    "inline_code": r"(?P<code>`(?P<content_code>.*?)`)",
}
# --- STYLE MAPPING ---
DEFAULT_MAPPING_JSON = {
    "code_block": {"panel_border_style": "style_code_panel_border", "panel_title_style": "style_code_panel_title", "syntax_theme": "default"},
    "blockquote": {"panel_border_style": "style_quote_panel_border", "content_style": "style_blockquote_content"},
    "list_block": {"guide_style": "style_list_guide"},
    "header_numbered": "style_header_numbered", "header1": "style_header1", "header2": "style_header2", "header3": "style_header3",
    "horizontal_rule": "style_hr", "key_value_colon": "style_key_value_line",
    "list_item_bullet": "style_list_level", "list_item_numbered": "style_list_level",
    "default_text": "style_default",
    # Implicit mapping for inline styles:
    # inline_bold_* -> style_inline_bold
    # inline_italic_* -> style_inline_italic
    # inline_code -> style_inline_code
}
# --- DEFAULT STYLES (styles.json) ---
# Default theme based on a GREENISH palette
DEFAULT_STYLES_JSON: Dict[str, StyleDefinition] = {
    # Block Styles
    "style_code_panel_border": "dim #006400",          # dim dark_green
    "style_code_panel_title": "italic #006400",         # italic dark_green
    "style_quote_panel_border": "dim #2E8B57",         # dim sea_green4
    "style_blockquote_content": "italic #2E8B57",        # italic sea_green4
    "style_list_guide": "dim #66CDAA",             # dim medium_aquamarine

    # Line Styles
    "style_header_numbered": "bold #3CB371",         # bold medium_sea_green
    "style_header1": "bold #00FF7F underline", # bold spring_green1 (brightest)
    "style_header2": "bold #00EE76",             # bold spring_green2
    "style_header3": "bold #2E8B57",             # bold sea_green4 (darker)
    "style_hr": "dim #8FBC8F",                 # dim dark_sea_green (matches default)
    "style_key_value_line": "default",             # Use default style

    # List Level Content Styles (Progressive greens)
    "style_list_level0": "#66CDAA",             # medium_aquamarine
    "style_list_level1": "#3CB371",             # medium_sea_green
    "style_list_level2": "#90EE90",             # light_green
    "style_list_level3": "#98FB98",             # pale_green1
    # Fallbacks for deeper levels
    "style_list_level4": "#66CDAA",
    "style_list_level5": "#3CB371",
    "style_list_level6": "#90EE90",
    "style_list_level7": "#98FB98",
    "style_list_level8": "#66CDAA",
    "style_list_level9": "#3CB371",

    # --- Inline Styles ---
    "style_inline_italic": "italic",             # Simple italic, inherits color

    "style_inline_bold": {                     # Dynamic bold based on context
        "attributes": "bold",
        "transform": {
            "adjust_brightness": 1.25,         # Moderate brightness increase
            "adjust_saturation": 1.1,          # Slight saturation increase
            "shift_hue": 5                     # Slight hue shift
        }
    },

    "style_inline_code": "#ADFF2F on grey19",      # green_yellow on dark grey background

    # Fallback Style
    "style_default": "#8FBC8F",                 # dark_sea_green (base green tone)
}

# ==============================================================================
# 3. Configuration Loading and Validation -- FUNCTIONS RESTORED HERE
# ==============================================================================
def ensure_config_dir(config_dir_path: Path, debug: bool = False):
    """Ensures the configuration directory exists, creating it if necessary."""
    if not config_dir_path.exists():
        if debug: print(f"DEBUG: Creating default config directory: {config_dir_path}", file=sys.stderr)
        try: config_dir_path.mkdir(parents=True, exist_ok=True)
        except OSError as e: print(f"ERROR: Failed to create config directory {config_dir_path}: {e}", file=sys.stderr); sys.exit(1)

def load_or_create_config(config_path: Path, default_content: dict, debug: bool = False) -> Dict:
    """Loads a config file, or creates it with default content if it doesn't exist."""
    if not config_path.exists():
        if debug: print(f"DEBUG: Creating default config file: {config_path}", file=sys.stderr)
        try:
            # Ensure parent directory exists before writing
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f: json.dump(default_content, f, indent=2)
        except IOError as e: print(f"ERROR: Failed creating config file {config_path}: {e}", file=sys.stderr); sys.exit(1)
        except OSError as e: print(f"ERROR: Failed creating parent directory for {config_path}: {e}", file=sys.stderr); sys.exit(1)
        return default_content
    else:
        if debug: print(f"DEBUG: Loading config file: {config_path}", file=sys.stderr)
        try:
            with open(config_path, "r", encoding="utf-8") as f: return json.load(f)
        except json.JSONDecodeError as e: print(f"ERROR: Invalid JSON in {config_path}: {e}", file=sys.stderr); print("Fix or delete file.", file=sys.stderr); sys.exit(1)
        except IOError as e: print(f"ERROR: Cannot read config file {config_path}: {e}", file=sys.stderr); sys.exit(1)
        except Exception as e: print(f"ERROR: Unexpected error loading {config_path}: {e}", file=sys.stderr); sys.exit(1)

def load_config_file(config_path: Path, debug: bool = False) -> Dict:
    """Loads a config file. Errors out if it doesn't exist."""
    if not config_path.exists():
        print(f"ERROR: Specified configuration file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    else:
        if debug: print(f"DEBUG: Loading config file: {config_path}", file=sys.stderr)
        try:
            with open(config_path, "r", encoding="utf-8") as f: return json.load(f)
        except json.JSONDecodeError as e: print(f"ERROR: Invalid JSON in {config_path}: {e}", file=sys.stderr); print("Fix or delete file.", file=sys.stderr); sys.exit(1)
        except IOError as e: print(f"ERROR: Cannot read config file {config_path}: {e}", file=sys.stderr); sys.exit(1)
        except Exception as e: print(f"ERROR: Unexpected error loading {config_path}: {e}", file=sys.stderr); sys.exit(1)


def _validate_style_definition(style_name: str, style_def: StyleDefinition, debug: bool) -> Tuple[bool, Optional[Style]]:
    """Validates a single style definition (string or dict)."""
    is_valid = True
    parsed_style: Optional[Style] = None
    try:
        if isinstance(style_def, str):
            parsed_style = Style.parse(style_def)
        elif isinstance(style_def, dict):
            attributes_str = style_def.get("attributes", "")
            transform_rules = style_def.get("transform")

            # Validate attributes part
            if not isinstance(attributes_str, str):
                print(f"ERROR: Style '{style_name}': 'attributes' must be a string.", file=sys.stderr); is_valid = False
            else:
                try:
                    # We only need to parse attributes here for validation;
                    # the actual combination happens during rendering.
                    parsed_style = Style.parse(attributes_str or "none") # Parse even if empty
                except StyleSyntaxError as e:
                    print(f"ERROR: Style '{style_name}': Invalid 'attributes' string '{attributes_str}': {e}", file=sys.stderr); is_valid = False

            # Validate transform part (if present)
            if transform_rules is not None:
                 # --- ADD colorsys check here under debug ---
                if debug:
                    # Print availability status only once per validation run if debug is on
                    if not hasattr(validate_configs, '_colorsys_checked'):
                         print(f"DEBUG: colorsys module is available for transforms: {colorsys is not None}", file=sys.stderr)
                         validate_configs._colorsys_checked = True # type: ignore
                # --- END added check ---

                if colorsys is None:
                     # Check only if colorsys is missing globally
                     if not hasattr(validate_configs, '_colorsys_warning_printed'): # Print only once
                         print(f"ERROR: Style '{style_name}' uses 'transform' but 'colorsys' module is not installed/importable.", file=sys.stderr)
                         validate_configs._colorsys_warning_printed = True # type: ignore
                     is_valid = False # Fail validation if transform used without colorsys
                elif not isinstance(transform_rules, dict):
                    print(f"ERROR: Style '{style_name}': 'transform' must be an object.", file=sys.stderr); is_valid = False
                else:
                    allowed_transforms = {"adjust_brightness", "adjust_saturation", "shift_hue"}
                    for key, value in transform_rules.items():
                        if key not in allowed_transforms:
                            if debug: print(f"DEBUG Warning: Style '{style_name}': Unknown transform key '{key}'. Ignoring.", file=sys.stderr)
                            continue
                        try:
                            float(value) # Check if value is numeric
                        except (ValueError, TypeError):
                            print(f"ERROR: Style '{style_name}': Transform value for '{key}' must be a number. Found: {value}", file=sys.stderr); is_valid = False
        else:
            print(f"ERROR: Style '{style_name}' has invalid type: {type(style_def)}. Must be string or object.", file=sys.stderr); is_valid = False

    except StyleSyntaxError as e: # Catch errors from Style.parse(str)
        print(f"ERROR: Invalid style '{style_name}': {e}", file=sys.stderr); is_valid = False
    except Exception as e:
        print(f"ERROR: Unexpected error parsing style '{style_name}': {e}", file=sys.stderr); is_valid = False

    return is_valid, parsed_style


def validate_configs(detection_rules: Dict, compiled_rules: Dict, style_mapping: Dict, styles: Dict[str, StyleDefinition], debug: bool = False) -> bool:
    """Validates all loaded configuration parts, including new style object syntax."""
    overall_valid = True
    special_mapping_keys = {"default_text", "code_block", "blockquote", "list_block"}
    list_content_mapping_keys = {"list_item_bullet", "list_item_numbered"}
    if debug: print("DEBUG: Validating configuration...", file=sys.stderr)
    # Reset flags at the start of validation
    if hasattr(validate_configs, '_colorsys_warning_printed'):
        delattr(validate_configs, '_colorsys_warning_printed')
    if hasattr(validate_configs, '_colorsys_checked'):
        delattr(validate_configs, '_colorsys_checked')


    # 1. Validate Compiled Rules
    for name, pattern in compiled_rules.items():
        if pattern is None: overall_valid = False # Error printed during compilation

    # 2. Validate Styles Dictionary & Build Set of Valid Style Names
    valid_styles: Dict[str, Optional[Style]] = {} # Store parsed style for attribute check later? Not strictly needed now.
    for style_name, style_def in styles.items():
        is_valid, _ = _validate_style_definition(style_name, style_def, debug)
        if not is_valid:
            overall_valid = False
        else:
            valid_styles[style_name] = None # Mark name as valid syntax-wise


    # 3. Validate Style Mapping
    mapped_rules_names = set(style_mapping.keys())
    defined_rule_names = set(detection_rules.keys())

    # Check for mappings to rules that don't exist (Warning)
    for rule_name in mapped_rules_names:
        if rule_name not in defined_rule_names and rule_name not in special_mapping_keys:
             # Exclude implicit inline mappings from this warning
             if not rule_name.startswith("style_inline_"):
                 if debug: print(f"DEBUG Warning: Rule '{rule_name}' mapped in mapping.json but has no detection rule.", file=sys.stderr)

    # Check if mapped styles actually exist in the styles dictionary
    for rule_name, mapping_value in style_mapping.items():
        if isinstance(mapping_value, str):
            # Skip list base names, checked later
            if rule_name in list_content_mapping_keys: continue
            style_name = mapping_value
            if style_name not in valid_styles:
                print(f"ERROR: Style '{style_name}' (mapped by rule '{rule_name}') not found or invalid in styles file.", file=sys.stderr); overall_valid = False
        elif isinstance(mapping_value, dict):
            # Check styles within block configurations (e.g., panel_border_style)
            for key, value in mapping_value.items():
                if key.endswith("_style"):
                    style_name = value
                    if not isinstance(style_name, str):
                        print(f"ERROR: Style name for '{key}' in '{rule_name}' mapping must be string.", file=sys.stderr); overall_valid = False
                    elif style_name not in valid_styles:
                        print(f"ERROR: Style '{style_name}' (for '{key}' in '{rule_name}') not found or invalid.", file=sys.stderr); overall_valid = False
                # Add validation for other block config keys like panel_padding, syntax_theme if needed
        else:
            print(f"ERROR: Invalid mapping value type for '{rule_name}'. Must be string or object.", file=sys.stderr); overall_valid = False

    # 4. Validate Special/Required Mappings & Styles
    # Default text
    default_text_map = style_mapping.get("default_text")
    if not default_text_map: print("ERROR: 'default_text' mapping missing in mapping.json.", file=sys.stderr); overall_valid = False
    elif not isinstance(default_text_map, str): print(f"ERROR: 'default_text' mapping must be a style name (string).", file=sys.stderr); overall_valid = False
    elif default_text_map not in valid_styles: print(f"ERROR: Default style '{default_text_map}' not found or invalid.", file=sys.stderr); overall_valid = False

    # List item levels (check level 0 for existence)
    for list_key in list_content_mapping_keys:
        base_style_name = style_mapping.get(list_key)
        if base_style_name:
            if not isinstance(base_style_name, str): print(f"ERROR: '{list_key}' mapping must be a base style name (string).", file=sys.stderr); overall_valid = False
            elif f"{base_style_name}0" not in valid_styles: print(f"ERROR: List style '{base_style_name}0' (level 0 for '{list_key}') not found or invalid.", file=sys.stderr); overall_valid = False

    # List block guide style
    list_block_config = style_mapping.get("list_block")
    if isinstance(list_block_config, dict):
        guide_style_name = list_block_config.get("guide_style")
        if not guide_style_name: print(f"ERROR: 'list_block' mapping missing 'guide_style'.", file=sys.stderr); overall_valid = False
        elif not isinstance(guide_style_name, str): print(f"ERROR: 'guide_style' in 'list_block' must be string.", file=sys.stderr); overall_valid = False
        elif guide_style_name not in valid_styles: print(f"ERROR: List guide style '{guide_style_name}' not found or invalid.", file=sys.stderr); overall_valid = False

    # Check implicit inline style definitions exist
    for inline_style_name in ["style_inline_bold", "style_inline_italic", "style_inline_code"]:
         if inline_style_name not in valid_styles:
             # Provide a more helpful error if the style definition itself was the problem
             if inline_style_name in styles: # Check if key exists but value was invalid
                 print(f"ERROR: Required inline style '{inline_style_name}' has invalid definition in styles file.", file=sys.stderr)
             else: # Key is missing entirely
                 print(f"ERROR: Required inline style '{inline_style_name}' not found in styles file.", file=sys.stderr)
             overall_valid = False


    # Final Verdict
    if overall_valid:
        if debug: print("DEBUG: Configuration validated successfully.", file=sys.stderr)
    else: print("Configuration validation failed. Please fix errors.", file=sys.stderr)
    return overall_valid

# load_all_configs uses the functions defined above
def load_all_configs(config_dir: str, style_filename: str, debug: bool = False) -> Tuple[Dict[str, Optional[re.Pattern]], Dict, Dict[str, StyleDefinition]]:
    """Loads all config files, using the specified style filename."""
    config_dir_path = Path(config_dir).expanduser()
    ensure_config_dir(config_dir_path, debug=debug) # Now defined

    detection_path = config_dir_path / "detection.json"
    mapping_path = config_dir_path / "mapping.json"

    # --- Determine Style Path ---
    style_path_arg = Path(style_filename).expanduser() # Expand potential ~

    # Check if the style argument is an absolute path or exists relative to CWD
    # Use resolve() to get absolute path for comparison consistency
    current_working_dir = Path.cwd()
    resolved_style_path_arg = (current_working_dir / style_path_arg).resolve()

    if style_path_arg.is_absolute():
         styles_path = style_path_arg.resolve()
         if debug: print(f"DEBUG: Using absolute style path: {styles_path}", file=sys.stderr)
    elif resolved_style_path_arg.exists() and resolved_style_path_arg.is_file():
         # Check relative to CWD *after* checking absolute
         styles_path = resolved_style_path_arg
         if debug: print(f"DEBUG: Using style path relative to CWD: {styles_path}", file=sys.stderr)
    else:
        # Assume it's a filename within the config directory (original behavior)
        styles_path = (config_dir_path / style_filename).resolve()
        if debug: print(f"DEBUG: Looking for style '{style_filename}' in config dir: {config_dir_path}", file=sys.stderr)
    # --- End Style Path Determination ---

    # --- Load detection/mapping (use config_dir_path) ---
    detection_rules_raw = load_or_create_config(detection_path, DEFAULT_DETECTION_JSON, debug=debug)
    if not isinstance(detection_rules_raw, dict):
        print(f"ERROR: {detection_path} must contain a JSON object.", file=sys.stderr); sys.exit(1)
    style_mapping = load_or_create_config(mapping_path, DEFAULT_MAPPING_JSON, debug=debug)
    if not isinstance(style_mapping, dict):
        print(f"ERROR: {mapping_path} must contain a JSON object.", file=sys.stderr); sys.exit(1)

    # --- Load styles using the determined styles_path ---
    styles: Dict[str, StyleDefinition]
    # Special handling only if the *default filename* 'styles.json' was requested
    # AND it resolves to the default config directory location
    is_default_style_in_default_dir = (
         style_filename == "styles.json" and
         styles_path == (config_dir_path / "styles.json").resolve() # Compare resolved paths
    )

    if is_default_style_in_default_dir:
        # Only create the default styles.json if it's the default name AND in the default location AND missing
        styles = load_or_create_config(styles_path, DEFAULT_STYLES_JSON, debug=debug)
    else:
        # If a custom style file is requested (by name or path), load it but DON'T create it if missing
        styles = load_config_file(styles_path, debug=debug) # load_config_file already errors if not found

    if not isinstance(styles, dict):
        print(f"ERROR: {styles_path} must contain a JSON object.", file=sys.stderr); sys.exit(1)

    # --- Compile Rules ---
    compiled_rules: Dict[str, Optional[re.Pattern]] = {}
    for name, pattern_str in detection_rules_raw.items():
        try:
            if not isinstance(pattern_str, str):
                 if debug: print(f"DEBUG Warning: Value for rule '{name}' not string. Skipping.", file=sys.stderr)
                 compiled_rules[name] = None; continue
            compiled_rules[name] = re.compile(pattern_str)
        except re.error as e: print(f"ERROR: Syntax Error in regex '{name}': {e}", file=sys.stderr); compiled_rules[name] = None
        except TypeError: print(f"ERROR: Type Error compiling regex '{name}'.", file=sys.stderr); compiled_rules[name] = None

    # --- Validate ---
    if not validate_configs(detection_rules_raw, compiled_rules, style_mapping, styles, debug=debug):
        sys.exit(1)

    return compiled_rules, style_mapping, styles


# ==============================================================================
# 4. Helper Functions
# ==============================================================================
# get_indent_level, get_panel_padding remain the same
def get_indent_level(line: str, indent_width: int = 2) -> int:
    leading_spaces = len(line) - len(line.lstrip(" "))
    if indent_width <= 0: indent_width = 2
    return max(0, leading_spaces // indent_width)

def get_panel_padding(config_value: Any, default: Tuple[int, int] = (0, 1)) -> Tuple[int, int]:
    try:
        if isinstance(config_value, list) and len(config_value) == 2 and all(isinstance(p, int) for p in config_value): return tuple(config_value) # type: ignore
    except: pass
    return default

def _apply_transform(base_color: Optional[Color], transform_rules: Optional[Dict], *, debug: bool = False) -> Optional[Color]:
    """Applies color transformations (brightness, saturation, hue) based on rules."""
    if not base_color or not transform_rules or colorsys is None:
        if debug: print(f"DEBUG Transform: Skipping - BaseColor={base_color}, HasTransformRules={transform_rules is not None}, HasColorsys={colorsys is not None}", file=sys.stderr)
        return base_color

    # Include type value in initial debug message
    if debug: print(f"DEBUG Transform: Attempting transform. BaseColor={base_color}, Type={base_color.type}, TypeValue={int(base_color.type)}, Rules={transform_rules}", file=sys.stderr)

    rgb_triplet: Optional[Tuple[int, int, int]] = None
    # --- Using Integer values for ColorType comparison as workaround ---
    # Assuming standard Rich enum values: DEFAULT=0, SYSTEM=1, EIGHT_BIT=2, TRUECOLOR=3, STANDARD=4
    color_type_value = int(base_color.type)

    # Safe check using integer values
    is_truecolor = color_type_value == 3 # Assuming TRUECOLOR is 3
    is_default = color_type_value == 0   # Assuming DEFAULT is 0
    is_system = color_type_value == 1    # Assuming SYSTEM is 1

    if debug: print(f"DEBUG Transform: Type Value Checks - IsTruecolor(3)={is_truecolor}, IsDefault(0)={is_default}, IsSystem(1)={is_system}", file=sys.stderr)

    try:
        if is_default:
            if debug: print(f"DEBUG Transform: Cannot transform DEFAULT color (value 0).", file=sys.stderr)
            return base_color
        elif is_system:
            if debug: print(f"DEBUG Transform: Cannot transform SYSTEM color (value 1).", file=sys.stderr)
            return base_color
        elif is_truecolor:
             # Directly use the triplet if type value matches TRUECOLOR (3)
             if debug: print(f"DEBUG Transform: Accessing .triplet for TRUECOLOR (value 3)", file=sys.stderr)
             rgb_triplet = base_color.triplet
             if debug: print(f"DEBUG Transform: Using existing triplet {rgb_triplet}", file=sys.stderr)
        else: # For other types (STANDARD=4, EIGHT_BIT=2, etc.)
            if debug: print(f"DEBUG Transform: Attempting get_truecolor() for unknown type value {color_type_value}", file=sys.stderr)
            rgb_triplet = base_color.get_truecolor() # This might still fail if get_truecolor internally has issues
            if debug: print(f"DEBUG Transform: get_truecolor() returned {rgb_triplet}", file=sys.stderr)

    except AttributeError as ae:
         # Keep the check for the specific internal error just in case
         if "'ColorType' has no attribute 'SYSTEM'" in str(ae): # Check the specific error message
             if debug: print(f"DEBUG Transform: Caught expected AttributeError ('SYSTEM' missing), cannot get RGB for {base_color}.", file=sys.stderr)
         else:
             if debug:
                 print(f"DEBUG Transform: Caught UNEXPECTED AttributeError getting RGB for {base_color}: {ae}", file=sys.stderr)
                 traceback.print_exc(file=sys.stderr)
         return base_color
    except Exception as e:
         if debug: print(f"DEBUG Transform: Warning - Could not get RGB for base color {base_color}: {e}", file=sys.stderr)
         return base_color

    if not rgb_triplet:
         if debug: print(f"DEBUG Transform: Failed to obtain RGB triplet for base color {base_color} after checks.", file=sys.stderr)
         return base_color

    # --- Transformation Logic ---
    if debug: print(f"DEBUG Transform: Base RGB = {rgb_triplet}", file=sys.stderr)
    # Normalize RGB to 0.0-1.0 for colorsys
    r, g, b = [x / 255.0 for x in rgb_triplet]
    try:
        h, l, s = colorsys.rgb_to_hls(r, g, b) # Use HLS (Lightness)
        if debug: print(f"DEBUG Transform: Initial HLS=({h:.3f}, {l:.3f}, {s:.3f})", file=sys.stderr)

        l_orig, s_orig, h_orig = l, s, h # Store original for comparison

        # Apply Brightness Adjustment
        if "adjust_brightness" in transform_rules:
            try:
                multiplier = float(transform_rules["adjust_brightness"])
                l = max(0.0, min(1.0, l * multiplier)) # Multiply and clamp
            except (ValueError, TypeError):
                 if debug: print(f"DEBUG Transform: Invalid value for adjust_brightness: {transform_rules['adjust_brightness']}", file=sys.stderr)


        # Apply Saturation Adjustment
        if "adjust_saturation" in transform_rules:
             try:
                 multiplier = float(transform_rules["adjust_saturation"])
                 s = max(0.0, min(1.0, s * multiplier)) # Multiply and clamp
             except (ValueError, TypeError):
                 if debug: print(f"DEBUG Transform: Invalid value for adjust_saturation: {transform_rules['adjust_saturation']}", file=sys.stderr)


        # Apply Hue Shift
        if "shift_hue" in transform_rules:
             try:
                 degrees = float(transform_rules["shift_hue"])
                 h = (h + (degrees / 360.0)) % 1.0 # Add shift and wrap (0.0 to 1.0)
             except (ValueError, TypeError):
                 if debug: print(f"DEBUG Transform: Invalid value for shift_hue: {transform_rules['shift_hue']}", file=sys.stderr)


        # Check if values actually changed before printing adjusted
        if l != l_orig or s != s_orig or h != h_orig:
            if debug: print(f"DEBUG Transform: Adjusted HLS=({h:.3f}, {l:.3f}, {s:.3f}) (Orig L={l_orig:.3f}, S={s_orig:.3f}, H={h_orig:.3f})", file=sys.stderr)
        elif debug:
            if debug: print(f"DEBUG Transform: HLS values unchanged after adjustments.", file=sys.stderr)


        # Convert back to RGB
        new_r, new_g, new_b = colorsys.hls_to_rgb(h, l, s)

        # Denormalize back to 0-255 and round correctly
        final_rgb = tuple(max(0, min(255, int(x * 255.0 + 0.5))) for x in (new_r, new_g, new_b))

        if debug: print(f"DEBUG Transform: Final RGB = {final_rgb}", file=sys.stderr)
        # Add note if color didn't change (useful for debugging subtle transforms)
        if final_rgb == rgb_triplet and debug:
             print(f"DEBUG Transform: Note - Final RGB is same as Base RGB.", file=sys.stderr)

        # Construct ColorTriplet before creating Color
        new_triplet = ColorTriplet(red=final_rgb[0], green=final_rgb[1], blue=final_rgb[2])
        if debug: print(f"DEBUG Transform: Returning Color from new triplet {new_triplet}", file=sys.stderr)
        # Return the new Color object using the ColorTriplet
        return Color.from_triplet(new_triplet)

    except Exception as e: # Catch errors during HLS conversion/adjustment
        if debug:
            print(f"ERROR applying color transform HLS logic: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        return base_color # Return original color on error

# --- HELPER for Inline Markup ---
def process_inline_markup(text_content: str, base_style: str, styles: Dict[str, StyleDefinition], compiled_rules: Dict[str, Optional[re.Pattern]], *, debug: bool = False) -> Text:
    """Processes inline markup (bold, italic, code) supporting transformations."""
    output_text = Text("", style=base_style)
    try:
        parsed_base_style = Style.parse(base_style)
        base_color = parsed_base_style.color
        if debug: print(f"\nDEBUG process_inline: Input='{text_content[:30]}...', BaseStyle='{base_style}', ParsedBaseStyle='{parsed_base_style}'", file=sys.stderr)
    except Exception as e:
        print(f"ERROR parsing base style '{base_style}': {e}", file=sys.stderr)
        output_text.append(text_content)
        return output_text

    # --- Regex Setup ---
    inline_rule_map_defs = {
        "bold_star": styles.get("style_inline_bold", "bold"),
        "bold_under": styles.get("style_inline_bold", "bold"),
        "italic_star": styles.get("style_inline_italic", "italic"),
        "italic_under": styles.get("style_inline_italic", "italic"),
        "code": styles.get("style_inline_code", "default"),
    }
    inline_patterns = [
        compiled_rules.get("inline_code"),
        compiled_rules.get("inline_bold_star"), compiled_rules.get("inline_bold_under"),
        compiled_rules.get("inline_italic_star"), compiled_rules.get("inline_italic_under"),
    ]
    valid_inline_patterns = [p for p in inline_patterns if p]
    if not valid_inline_patterns:
        output_text.append(text_content); return output_text
    combined_pattern = "|".join(p.pattern for p in valid_inline_patterns)
    try: finder_re = re.compile(combined_pattern)
    except re.error as e:
        print(f"ERROR: Invalid combined inline regex: {e}", file=sys.stderr)
        output_text.append(text_content); return output_text

    # --- Processing Loop ---
    last_end = 0
    for match in finder_re.finditer(text_content):
        start, end = match.span()
        match_group_name = match.lastgroup

        if start > last_end:
            plain_bit = text_content[last_end:start]
            if plain_bit: output_text.append(plain_bit)

        content = None
        final_inline_style: Optional[Style] = None

        if match_group_name and match_group_name in inline_rule_map_defs:
            style_definition = inline_rule_map_defs[match_group_name]
            content_group_name = f"content_{match_group_name}"
            try: content = match.group(content_group_name)
            except IndexError: content = None

            if content is not None:
                if debug: print(f"DEBUG process_inline: Matched '{match_group_name}', Content='{content}', Def='{style_definition}'", file=sys.stderr)
                try:
                    inline_style_attributes = Style() # Style containing only attributes from definition
                    inline_style_color: Optional[Color] = None # Color explicitly defined in definition
                    transform_rules = None
                    calculated_color: Optional[Color] = None

                    # 1. Parse definition and extract parts
                    if isinstance(style_definition, dict):
                        attributes_str = style_definition.get("attributes", "")
                        transform_rules = style_definition.get("transform")
                        if attributes_str:
                            parsed_attrs_style = Style.parse(attributes_str)
                            # Separate attributes from potential color in the 'attributes' string
                            inline_style_attributes = Style(
                                bold=parsed_attrs_style.bold,
                                italic=parsed_attrs_style.italic,
                                underline=parsed_attrs_style.underline,
                                blink=parsed_attrs_style.blink,
                                blink2=parsed_attrs_style.blink2,
                                reverse=parsed_attrs_style.reverse,
                                conceal=parsed_attrs_style.conceal,
                                strike=parsed_attrs_style.strike,
                                underline2=parsed_attrs_style.underline2,
                                frame=parsed_attrs_style.frame,
                                encircle=parsed_attrs_style.encircle,
                                overline=parsed_attrs_style.overline,
                            )
                            inline_style_color = parsed_attrs_style.color # Color defined within 'attributes'

                    elif isinstance(style_definition, str):
                        parsed_attrs_style = Style.parse(style_definition)
                        # Separate attributes and color
                        inline_style_attributes = Style( # Copy attributes
                             bold=parsed_attrs_style.bold, italic=parsed_attrs_style.italic, underline=parsed_attrs_style.underline,
                             blink=parsed_attrs_style.blink, blink2=parsed_attrs_style.blink2, reverse=parsed_attrs_style.reverse,
                             conceal=parsed_attrs_style.conceal, strike=parsed_attrs_style.strike, underline2=parsed_attrs_style.underline2,
                             frame=parsed_attrs_style.frame, encircle=parsed_attrs_style.encircle, overline=parsed_attrs_style.overline
                        )
                        inline_style_color = parsed_attrs_style.color
                    else:
                         inline_style_attributes = Style.null()


                    # 2. Apply transformation if rules exist
                    calculated_color = _apply_transform(base_color, transform_rules, debug=debug)
                    if debug: print(f"DEBUG process_inline: BaseColor={base_color}, DefColor={inline_style_color}, CalculatedColor={calculated_color}", file=sys.stderr)


                    # 3. Combine Styles: Base + Inline Attributes + Final Color
                    # Start with the full base style
                    final_inline_style = parsed_base_style

                    # Add the attributes defined by the inline style (bold, italic, etc.)
                    final_inline_style += inline_style_attributes

                    # Determine the final color: Calculated > Definition > Base (already included)
                    final_color_to_apply: Optional[Color] = None
                    if calculated_color:
                        final_color_to_apply = calculated_color
                    elif inline_style_color:
                        final_color_to_apply = inline_style_color

                    # Apply the final color if one was determined (overrides base color)
                    if final_color_to_apply:
                         final_inline_style = final_inline_style + Style(color=final_color_to_apply)
                    # Else: color remains inherited from parsed_base_style


                    # Preserve links/meta (important to do *after* color/attr combination)
                    # Use base link/meta only if final style doesn't have them
                    if parsed_base_style.link and not final_inline_style.link: final_inline_style += Style(link=parsed_base_style.link)
                    if parsed_base_style.link_id and not final_inline_style.link_id: final_inline_style += Style(link_id=parsed_base_style.link_id)
                    # Meta usually combines, but let's be explicit if needed
                    # if parsed_base_style.meta and not final_inline_style.meta: final_inline_style += Style(meta=parsed_base_style.meta)

                    if debug: print(f"DEBUG process_inline: FinalStyle='{final_inline_style}', FinalAttrs=(B={final_inline_style.bold},I={final_inline_style.italic},U={final_inline_style.underline}), FinalColor='{final_inline_style.color}'", file=sys.stderr)
                    output_text.append(content, style=final_inline_style or Style.null())

                except StyleSyntaxError as e_style:
                     print(f"ERROR: Invalid style definition '{style_definition}' for {match_group_name}: {e_style}", file=sys.stderr)
                     output_text.append(content)
                except Exception as e_proc:
                     print(f"ERROR: Processing inline part '{content}' for {match_group_name}: {e_proc}", file=sys.stderr)
                     traceback.print_exc(file=sys.stderr)
                     output_text.append(content)

        if content is None:
            raw_match_text = match.group(0)
            if raw_match_text: output_text.append(raw_match_text)

        last_end = end

    if last_end < len(text_content):
        remaining_bit = text_content[last_end:]
        if remaining_bit: output_text.append(remaining_bit)

    return output_text

# ==============================================================================
# 5. Main Styling Logic
# ==============================================================================
def apply_styles(
    text_content: str,
    compiled_rules: Dict[str, Optional[re.Pattern]],
    style_mapping: Dict,
    styles: Dict[str, StyleDefinition], # Use type alias
    console: Console,
    debug: bool = False, # Keep debug flag here
    keep_markup: bool = False
):
    renderables: List = []
    # --- State Variables ---
    in_code_block = False; code_block_content: List[str] = []; code_block_language: str = ""
    code_block_config: Dict = style_mapping.get("code_block", {})
    in_blockquote = False; blockquote_content: List[str] = []
    blockquote_config: Dict = style_mapping.get("blockquote", {})
    in_list_block = False; current_tree: Optional[Tree] = None
    node_stack: List[Tuple[int, Any]] = []
    list_block_config: Dict = style_mapping.get("list_block", {})

    # --- Style Lookups Helper ---
    def _get_style_str(style_name: str, fallback: str = "default") -> str:
        """Gets the style string, handling dict definitions for simple parsing."""
        style_def = styles.get(style_name, fallback)
        if isinstance(style_def, dict):
            # Return the 'attributes' string part if defined, else fallback
            return style_def.get("attributes", fallback)
        # If it's already a string or fallback needed
        return style_def if isinstance(style_def, str) else fallback

    # --- Parse necessary styles ---
    list_guide_style_name = list_block_config.get("guide_style", "")
    list_guide_style_str = _get_style_str(list_guide_style_name, "default") # Get string for Tree
    try:
        list_guide_style_parsed = Style.parse(list_guide_style_str)
    except Exception: list_guide_style_parsed = Style.parse("default") # Fallback parsed

    default_style_name = style_mapping.get("default_text", "style_default")
    # Get the base string definition for default, needed by process_inline_markup
    default_style_str = _get_style_str(default_style_name, "default")


    # --- Other Setup ---
    indent_width = 2; max_list_levels_styled = 10
    lines = text_content.splitlines()
    code_fence_rule = compiled_rules.get("code_block_fence")
    blockquote_rule = compiled_rules.get("blockquote_start")
    list_bullet_rule = compiled_rules.get("list_item_bullet")
    list_numbered_rule = compiled_rules.get("list_item_numbered")
    hr_rule = compiled_rules.get("horizontal_rule")
    header_numbered_rule = compiled_rules.get("header_numbered")
    header1_rule = compiled_rules.get("header1")
    header2_rule = compiled_rules.get("header2")
    header3_rule = compiled_rules.get("header3")

    # --- Finalize Helper Functions ---
    def finalize_tree():
        nonlocal in_list_block, current_tree, node_stack
        if current_tree: renderables.append(current_tree)
        in_list_block = False; current_tree = None; node_stack = []


    def finalize_blockquote():
        nonlocal in_blockquote, blockquote_content
        if blockquote_content:
            panel_border_style_name=blockquote_config.get("panel_border_style", "default")
            content_style_name=blockquote_config.get("content_style", "default")
            panel_padding_config=blockquote_config.get("panel_padding")

            panel_border_style_str = _get_style_str(panel_border_style_name) # Get string
            content_style_str = _get_style_str(content_style_name)          # Get string
            panel_padding=get_panel_padding(panel_padding_config)

            quote_str="\n".join(blockquote_content)
            try:
                # Pass the style *string* AND debug flag to process_inline_markup
                quote_text = process_inline_markup(quote_str, content_style_str, styles, compiled_rules, debug=debug)
                panel = Panel(quote_text, border_style=panel_border_style_str, padding=panel_padding)
                renderables.append(panel)
            except Exception as e:
                if debug: print(f"DEBUG Warning: Error rendering blockquote: {e}", file=sys.stderr)
                renderables.append(Panel(quote_str, border_style=panel_border_style_str, padding=panel_padding)) # Render raw on error
        in_blockquote = False; blockquote_content = []

    def finalize_code_block():
        nonlocal in_code_block, code_block_content, code_block_language
        if code_block_content:
            panel_border_style_name=code_block_config.get("panel_border_style", "default")
            panel_title_style_name=code_block_config.get("panel_title_style", "default")
            syntax_theme=code_block_config.get("syntax_theme", "default")
            panel_padding_config=code_block_config.get("panel_padding")

            panel_border_style_str = _get_style_str(panel_border_style_name) # Get string
            panel_title_style_str = _get_style_str(panel_title_style_name)   # Get string
            panel_padding=get_panel_padding(panel_padding_config)

            code_str="\n".join(code_block_content)
            renderable_content: Any
            can_highlight = False
            # --- Pygments Highlighting Logic ---
            if pygments and code_block_language and code_block_language != "default":
                try:
                    get_lexer_by_name(code_block_language)
                    can_highlight = True
                except ClassNotFound: pass # Ignore if lexer not found
                except Exception: pass # Ignore other pygments errors

            if can_highlight:
                renderable_content = Syntax(code_str, code_block_language, theme=syntax_theme, line_numbers=False, word_wrap=False, background_color="default", dedent=False)
            else:
                # Use default style string for non-highlighted code
                renderable_content = Text(code_str, style=_get_style_str("style_default"))

            # --- Panel Creation ---
            panel = Panel(renderable_content, title=code_block_language if code_block_language != "default" else None, title_align="left", border_style=panel_border_style_str, padding=panel_padding)
            if panel.title:
                 try: panel.title = Text(str(panel.title), style=panel_title_style_str)
                 except Exception: panel.title = Text(str(panel.title)) # Fallback title
            renderables.append(panel)
        in_code_block = False; code_block_content = []; code_block_language = ""


    # --- Line-by-Line Processing Loop ---
    for i, line in enumerate(lines):
        # --- Block Handling (Code, Quote - same logic as before) ---
        fence_match = code_fence_rule.match(line) if code_fence_rule else None
        if fence_match:
            if in_list_block: finalize_tree()
            if in_blockquote: finalize_blockquote()
            if not in_code_block:
                in_code_block = True; code_block_language = fence_match.group(1) or "default"; code_block_content = []; continue
            else: finalize_code_block(); continue
        if in_code_block: code_block_content.append(line); continue

        is_blockquote_line = blockquote_rule.match(line) if blockquote_rule else None
        if is_blockquote_line:
            if in_list_block: finalize_tree()
            if not in_blockquote: in_blockquote = True; blockquote_content = []
            quote_line_content = re.sub(r"^\s*>\s?", "", line); blockquote_content.append(quote_line_content); continue
        elif in_blockquote: finalize_blockquote()

        # --- List Handling ---
        list_match = None; is_bullet = False
        if list_bullet_rule and (match := list_bullet_rule.match(line)): list_match = match; is_bullet = True;
        if not list_match and list_numbered_rule and (match := list_numbered_rule.match(line)): list_match = match; is_bullet = False;

        if list_match:
            # Finalize other blocks if starting list
            # if in_blockquote: finalize_blockquote() # Handled above

            base_style_key = "list_item_bullet" if is_bullet else "list_item_numbered"
            base_style_name = style_mapping.get(base_style_key) # e.g., "style_list_level"

            if base_style_name and isinstance(base_style_name, str) and len(list_match.groups()) >= 2:
                indent_str = list_match.group(1); content_str = list_match.group(2); current_level = get_indent_level(indent_str + (" " if is_bullet else "  "), indent_width)

                if not in_list_block: # Starting new list block
                    in_list_block = True
                    # Use the parsed Style object for the Tree guide
                    current_tree = Tree("", guide_style=list_guide_style_parsed)
                    node_stack = [(-1, current_tree)]

                while node_stack and node_stack[-1][0] >= current_level: node_stack.pop()

                if not node_stack:
                    if debug: print(f"DEBUG Warning: List parsing error - node stack empty: {line}", file=sys.stderr)
                    finalize_tree(); # Reset and fall through
                else:
                    parent_level, parent_node = node_stack[-1]
                    # Get style *string* for this level for process_inline_markup
                    level_idx = current_level % max_list_levels_styled
                    style_name = f"{base_style_name}{level_idx}"
                    # Get the style string, falling back to level0 or default_style_str
                    content_style_str = _get_style_str(style_name, fallback=_get_style_str(f"{base_style_name}0", default_style_str))

                    try:
                        text_to_process = content_str # Default: just content
                        if keep_markup:
                             # Simplified prefix logic for keep_markup
                             prefix = ("* " if is_bullet else f"{' '*(indent_width*current_level)}{current_level+1}. ") # Approximate prefix
                             text_to_process = prefix + content_str

                        # Process content with its specific style string AND PASS DEBUG FLAG
                        node_label = process_inline_markup(text_to_process, content_style_str, styles, compiled_rules, debug=debug)
                        new_node = parent_node.add(node_label)
                        node_stack.append((current_level, new_node))
                        continue # Handled as list item

                    except Exception as e:
                        print(f"ERROR Adding node to tree: {e}", file=sys.stderr); traceback.print_exc(file=sys.stderr)
                        finalize_tree() # Reset and fall through
            else:
                 if debug: print(f"DEBUG Warning: List regex matched but invalid mapping/groups: {line[:50]}...", file=sys.stderr)
                 if in_list_block: finalize_tree();
        elif in_list_block: # Current line not list item, finalize
             finalize_tree()

        # --- Non-Block, Non-List Lines (Headers, HR, Generic) ---
        matched_line = False

        # Headers
        header_match_handled = False
        header_rules = [
            (header_numbered_rule, "header_numbered", (lambda m: f"{m.group(1)}. {m.group(2)}")),
            (header1_rule, "header1", (lambda m: m.group(1))),
            (header2_rule, "header2", (lambda m: m.group(1))),
            (header3_rule, "header3", (lambda m: m.group(1))),
        ]
        for rule, map_key, content_extractor in header_rules:
             if rule and (match := rule.match(line)):
                 style_name = style_mapping.get(map_key)
                 if style_name:
                     style_str = _get_style_str(style_name, default_style_str) # Get style string
                     text_to_process = line if keep_markup else content_extractor(match)
                     # Pass debug flag
                     renderables.append(process_inline_markup(text_to_process, style_str, styles, compiled_rules, debug=debug))
                     matched_line = True; header_match_handled = True; break # Stop after first header match

        # Horizontal Rule
        if not header_match_handled and hr_rule and hr_rule.match(line):
            hr_style_name = style_mapping.get("horizontal_rule", "default")
            hr_style_str = _get_style_str(hr_style_name, "default") # Get style string
            try: renderables.append(Rule(style=hr_style_str)); matched_line = True
            except Exception as e:
                 print(f"Warning: Failed to render Rule with style '{hr_style_str}': {e}", file=sys.stderr)
                 renderables.append(Rule()) # Fallback rule


        # Other Generic Line Rules
        if not matched_line:
             skipped_rules = {
                 "code_block_fence", "blockquote_start", "list_item_bullet", "list_item_numbered",
                 "header_numbered", "header1", "header2", "header3", "horizontal_rule",
                 # Inline rules are handled by process_inline_markup
             }
             for name, pattern in compiled_rules.items():
                 # Skip detection rules that are handled specifically or are inline markers
                 if name in skipped_rules or pattern is None or name.startswith("inline_"): continue;
                 match = pattern.match(line)
                 if match:
                     style_name = style_mapping.get(name)
                     if style_name:
                          style_str = _get_style_str(style_name, default_style_str) # Get style string
                          # Pass debug flag
                          renderables.append(process_inline_markup(line, style_str, styles, compiled_rules, debug=debug)); matched_line = True; break;
                     # else: fall through if rule matched but no mapping

        # --- Default Fallback ---
        if not matched_line:
             # Pass the default style string AND debug flag
             renderables.append(process_inline_markup(line, default_style_str, styles, compiled_rules, debug=debug))

    # --- End of Input Finalization ---
    if in_list_block: finalize_tree()
    if in_blockquote: finalize_blockquote()
    if in_code_block: finalize_code_block()

    # --- Print All Renderables ---
    for item in renderables:
        console.print(item)

# ==============================================================================
# 6. Main Execution Block
# ==============================================================================
# main function remains the same
def main():
    parser = argparse.ArgumentParser(
        description="Apply styles to text input based on configurable rules.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config-dir",
        default="~/.config/llm-style",
        help="Directory containing detection.json, mapping.json, and style JSON files."
    )
    parser.add_argument(
        "--style",
        default="styles.json",
        help="Filename or path of the style definitions JSON file. If not absolute/relative, assumed within config directory."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug/verbose output to stderr."
    )
    parser.add_argument(
        "--keep-markup",
        action="store_true",
        help="Keep original Markdown block characters (e.g., '#', '*', '>') in the output."
    )
    args = parser.parse_args()

    if sys.stdin.isatty() and not args.debug: # Allow debug mode even with TTY
        parser.print_usage(file=sys.stderr)
        print("Error: Input must be piped from another command.", file=sys.stderr)
        print("Example: llm 'prompt' | llm-style.py", file=sys.stderr)
        sys.exit(1)

    # Check for colorsys early if transforms might be used
    if colorsys is None:
        # Simple check if style file likely contains transform syntax
        has_transform = False
        # Determine potential style path (simplified check)
        style_path_arg = Path(args.style).expanduser()
        if style_path_arg.is_absolute():
            temp_styles_path = style_path_arg
        elif (Path.cwd() / style_path_arg).exists():
             temp_styles_path = Path.cwd() / style_path_arg
        else:
            temp_styles_path = Path(args.config_dir).expanduser() / args.style

        if temp_styles_path.exists():
            try:
                with open(temp_styles_path, 'r', encoding='utf-8') as f_check:
                    if '"transform":' in f_check.read(): has_transform = True
            except Exception: pass
        if has_transform:
            print("Warning: Style file may contain 'transform' rules, but the 'colorsys' module could not be imported. Transformations will be skipped.", file=sys.stderr)


    try:
        compiled_rules, style_mapping, styles = load_all_configs(
            args.config_dir,
            args.style, # Pass the style filename/path
            debug=args.debug
        )
    except SystemExit: sys.exit(1)
    except Exception as e:
        print(f"FATAL: Unexpected error loading/validating configuration: {e}", file=sys.stderr); traceback.print_exc(file=sys.stderr); sys.exit(1)

    try:
        input_text = sys.stdin.read()
    except Exception as e:
        print(f"Error reading standard input: {e}", file=sys.stderr); sys.exit(1)

    console = Console()
    try:
        apply_styles(
            input_text, compiled_rules, style_mapping, styles, console,
            debug=args.debug, keep_markup=args.keep_markup
        )
    except Exception as e:
        print(f"\n--- Unexpected Error During Styling ---", file=sys.stderr); print(f"Error: {e}", file=sys.stderr); traceback.print_exc(file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    main()