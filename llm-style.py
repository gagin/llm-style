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
from typing import List, Dict, Tuple, Optional, Any

# 1.1. Pygments Import (Optional)
# ------------------------------------------------------------------------------
try:
    import pygments
    from pygments.lexers import get_lexer_by_name
    from pygments.util import ClassNotFound
except ImportError:
    pygments = None; ClassNotFound = Exception; get_lexer_by_name = lambda *a, **k: (_ for _ in ()).throw(ClassNotFound()) # type: ignore

# 1.2. Rich Imports
# ------------------------------------------------------------------------------
from rich.console import Console, ConsoleOptions, RenderResult
from rich.text import Text
from rich.panel import Panel
from rich.syntax import Syntax
from rich.rule import Rule
from rich.style import Style
from rich.errors import StyleSyntaxError
from rich.tree import Tree
from rich.measure import Measurement

# ==============================================================================
# 2. Default Configuration Content
# ==============================================================================
# 2.1. Default Detection Rules (detection.json)
# ------------------------------------------------------------------------------
DEFAULT_DETECTION_JSON = {
    # Meta Rules
    "code_block_fence": r"^\s*```(\w*)", "blockquote_start": r"^\s*>",
    # Line Rules
    "header_numbered": r"^\*\*(\d+)\.\s+(.*?)\*\*$", "header1": r"^#\s+(.*)", "header2": r"^##\s+(.*)", "header3": r"^###\s+(.*)",
    "list_item_bullet": r"^(\s*)[-*+]\s+(.*)", "list_item_numbered": r"^(\s*)\d+\.\s+(.*)",
    "horizontal_rule": r"^\s*([-*_]){3,}\s*$", "key_value_colon": r"^\s*([\w\s-]+?)\s*:\s+(.*)",

    # --- Inline Rules (with NAMED groups, content is group 1 within) ---
    # MODIFICATION: Add explicit named group for CONTENT inside each inline rule (content_rulename)
    # Use *? (non-greedy zero-or-more) instead of +? to allow empty content like ** **
    "inline_bold_star": r"(?P<bold_star>\*\*(?P<content_bold_star>.*?)\*\*)",
    "inline_bold_under": r"(?P<bold_under>__(?P<content_bold_under>.*?)__)",
    "inline_italic_star": r"(?P<italic_star>\*(?P<content_italic_star>.*?)\*)",
    "inline_italic_under": r"(?P<italic_under>_(?P<content_italic_under>.*?)_)",
    "inline_code": r"(?P<code>`(?P<content_code>.*?)`)",
}

# NOTE: mapping.json defaults do not need changes for this fix.
# 2.2. Default Style Mapping (mapping.json)
DEFAULT_MAPPING_JSON = {
    "code_block": {"panel_border_style": "style_code_panel_border", "panel_title_style": "style_code_panel_title", "syntax_theme": "default"},
    "blockquote": {"panel_border_style": "style_quote_panel_border", "content_style": "style_blockquote_content"},
    "list_block": {"guide_style": "style_list_guide"},
    "header_numbered": "style_header_numbered", "header1": "style_header1", "header2": "style_header2", "header3": "style_header3",
    "horizontal_rule": "style_hr", "key_value_colon": "style_key_value_line",
    "list_item_bullet": "style_list_level", "list_item_numbered": "style_list_level",
    "default_text": "style_default",
}

# 2.3. Default Styles (styles.json) - This is the fallback if styles.json is missing
# ------------------------------------------------------------------------------
DEFAULT_STYLES_JSON = {
    # Default original theme (adjust if you prefer the calm theme as the hardcoded default)
    "style_code_panel_border": "dim blue",
    "style_code_panel_title": "italic blue",
    "style_quote_panel_border": "dim yellow",
    "style_blockquote_content": "italic yellow",
    "style_list_guide": "dim cyan",
    "style_header_numbered": "bold magenta",
    "style_header1": "bold bright_blue underline",
    "style_header2": "bold blue",
    "style_header3": "bold cyan",
    "style_hr": "dim",
    "style_key_value_line": "default",
    "style_list_level0": "green",
    "style_list_level1": "light_sea_green",
    "style_list_level2": "medium_spring_green",
    "style_list_level3": "spring_green1",
    "style_list_level4": "green",
    "style_list_level5": "light_sea_green",
    "style_list_level6": "medium_spring_green",
    "style_list_level7": "spring_green1",
    "style_list_level8": "green",
    "style_list_level9": "light_sea_green",
    "style_inline_bold": "bold",
    "style_inline_italic": "italic",
    "style_inline_code": "bright_black on grey30",
    "style_default": "tan",
}

# ==============================================================================
# 3. Configuration Loading and Validation
# ==============================================================================
def ensure_config_dir(config_dir_path: Path, debug: bool = False):
    if not config_dir_path.exists():
        if debug: print(f"DEBUG: Creating default config directory: {config_dir_path}", file=sys.stderr)
        try: config_dir_path.mkdir(parents=True, exist_ok=True)
        except OSError as e: print(f"ERROR: Failed to create config directory {config_dir_path}: {e}", file=sys.stderr); sys.exit(1)

def load_or_create_config(config_path: Path, default_content: dict, debug: bool = False):
    """Loads a config file, or creates it with default content if it doesn't exist."""
    if not config_path.exists():
        if debug: print(f"DEBUG: Creating default config file: {config_path}", file=sys.stderr)
        try:
            with open(config_path, "w", encoding="utf-8") as f: json.dump(default_content, f, indent=2)
        except IOError as e: print(f"ERROR: Failed creating config file {config_path}: {e}", file=sys.stderr); sys.exit(1)
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


def validate_configs(detection_rules: Dict, compiled_rules: Dict, style_mapping: Dict, styles: Dict, debug: bool = False) -> bool:
    is_valid = True; special_mapping_keys = {"default_text", "code_block", "blockquote", "list_block"}; list_content_mapping_keys = {"list_item_bullet", "list_item_numbered"}
    if debug: print("DEBUG: Validating configuration...", file=sys.stderr)
    for name, pattern in compiled_rules.items():
        if pattern is None: is_valid = False
    valid_styles = set()
    for style_name, style_def in styles.items():
        try:
            if not isinstance(style_def, str): print(f"ERROR: Style '{style_name}' must be string.", file=sys.stderr); is_valid = False; continue
            Style.parse(style_def); valid_styles.add(style_name)
        except StyleSyntaxError as e: print(f"ERROR: Invalid style '{style_name}': {e}", file=sys.stderr); is_valid = False
        except Exception as e: print(f"ERROR: Unexpected error parsing style '{style_name}': {e}", file=sys.stderr); is_valid = False
    mapped_rules_names = set(style_mapping.keys()); defined_rule_names = set(detection_rules.keys())
    for rule_name in mapped_rules_names:
        if rule_name not in defined_rule_names and rule_name not in special_mapping_keys:
             if debug: print(f"DEBUG Warning: Rule '{rule_name}' mapped but has no detection rule.", file=sys.stderr)
    for rule_name, mapping_value in style_mapping.items():
        if isinstance(mapping_value, str):
            if rule_name in list_content_mapping_keys: continue # List levels checked separately
            style_name = mapping_value
            if style_name not in valid_styles: print(f"ERROR: Style '{style_name}' (for rule '{rule_name}') not found/invalid.", file=sys.stderr); is_valid = False
        elif isinstance(mapping_value, dict):
            for key, value in mapping_value.items():
                if key.endswith("_style"):
                    style_name = value
                    if not isinstance(style_name, str): print(f"ERROR: Style name '{key}' in '{rule_name}' must be string.", file=sys.stderr); is_valid = False
                    elif style_name not in valid_styles: print(f"ERROR: Style '{style_name}' ('{key}' in '{rule_name}') not found/invalid.", file=sys.stderr); is_valid = False
                elif key == "panel_padding" and not (isinstance(value, list) and len(value) == 2 and all(isinstance(p, int) for p in value)):
                    if debug: print(f"DEBUG Warning: 'panel_padding' for '{rule_name}' should be [int, int]. Found: {value}", file=sys.stderr)
                elif key == "syntax_theme" and not isinstance(value, str):
                    if debug: print(f"DEBUG Warning: 'syntax_theme' for '{rule_name}' should be string. Found: {value}", file=sys.stderr)
        else: print(f"ERROR: Invalid mapping value for '{rule_name}'.", file=sys.stderr); is_valid = False
    default_text_map = style_mapping.get("default_text")
    if not default_text_map: print("ERROR: 'default_text' mapping missing.", file=sys.stderr); is_valid = False
    elif not isinstance(default_text_map, str): print(f"ERROR: 'default_text' mapping must be string.", file=sys.stderr); is_valid = False
    elif default_text_map not in valid_styles: print(f"ERROR: Default style '{default_text_map}' not found/invalid.", file=sys.stderr); is_valid = False
    for list_key in list_content_mapping_keys:
        base_style_name = style_mapping.get(list_key)
        if base_style_name:
            if not isinstance(base_style_name, str): print(f"ERROR: '{list_key}' mapping must be string.", file=sys.stderr); is_valid = False
            elif f"{base_style_name}0" not in valid_styles: print(f"ERROR: List style '{base_style_name}0' (level 0 for '{list_key}') not found/invalid.", file=sys.stderr); is_valid = False # Check level 0 exists
    list_block_config = style_mapping.get("list_block")
    if isinstance(list_block_config, dict):
        guide_style_name = list_block_config.get("guide_style")
        if not guide_style_name: print(f"ERROR: 'list_block' mapping missing 'guide_style'.", file=sys.stderr); is_valid = False
        elif not isinstance(guide_style_name, str): print(f"ERROR: 'guide_style' in 'list_block' must be string.", file=sys.stderr); is_valid = False
        elif guide_style_name not in valid_styles: print(f"ERROR: List guide style '{guide_style_name}' not found/invalid.", file=sys.stderr); is_valid = False
    if is_valid:
        if debug: print("DEBUG: Configuration validated successfully.", file=sys.stderr)
    else: print("Configuration validation failed. Please fix errors.", file=sys.stderr)
    return is_valid

def load_all_configs(config_dir: str, style_filename: str, debug: bool = False) -> Tuple[Dict[str, Optional[re.Pattern]], Dict, Dict]:
    """Loads all config files, using the specified style filename."""
    config_dir_path = Path(config_dir).expanduser()
    ensure_config_dir(config_dir_path, debug=debug)

    detection_path = config_dir_path / "detection.json"
    mapping_path = config_dir_path / "mapping.json"
    styles_path = config_dir_path / style_filename # Use the provided filename

    # Load detection rules (create default if missing)
    detection_rules_raw = load_or_create_config(detection_path, DEFAULT_DETECTION_JSON, debug=debug)
    if not isinstance(detection_rules_raw, dict):
        print(f"ERROR: {detection_path} must contain a JSON object.", file=sys.stderr); sys.exit(1)

    # Load style mapping (create default if missing)
    style_mapping = load_or_create_config(mapping_path, DEFAULT_MAPPING_JSON, debug=debug)
    if not isinstance(style_mapping, dict):
        print(f"ERROR: {mapping_path} must contain a JSON object.", file=sys.stderr); sys.exit(1)

    # Load styles
    styles: Dict
    if style_filename == "styles.json":
        # Only create the default styles.json if it's the one requested and missing
        styles = load_or_create_config(styles_path, DEFAULT_STYLES_JSON, debug=debug)
    else:
        # If a custom style file is requested, load it but DON'T create it if missing
        styles = load_config_file(styles_path, debug=debug)

    if not isinstance(styles, dict):
        print(f"ERROR: {styles_path} must contain a JSON object.", file=sys.stderr); sys.exit(1)

    # Compile detection rules
    compiled_rules: Dict[str, Optional[re.Pattern]] = {}
    for name, pattern_str in detection_rules_raw.items():
        try:
            if not isinstance(pattern_str, str):
                 if debug: print(f"DEBUG Warning: Value for rule '{name}' not string. Skipping.", file=sys.stderr)
                 compiled_rules[name] = None; continue
            compiled_rules[name] = re.compile(pattern_str)
        except re.error as e: print(f"ERROR: Syntax Error in regex '{name}': {e}", file=sys.stderr); compiled_rules[name] = None
        except TypeError: print(f"ERROR: Type Error compiling regex '{name}'.", file=sys.stderr); compiled_rules[name] = None

    # Validate the combined configuration
    if not validate_configs(detection_rules_raw, compiled_rules, style_mapping, styles, debug=debug):
        sys.exit(1)

    return compiled_rules, style_mapping, styles

# ==============================================================================
# 4. Helper Functions
# ==============================================================================
def get_indent_level(line: str, indent_width: int = 2) -> int:
    leading_spaces = len(line) - len(line.lstrip(" "))
    if indent_width <= 0: indent_width = 2
    return max(0, leading_spaces // indent_width)

def get_panel_padding(config_value: Any, default: Tuple[int, int] = (0, 1)) -> Tuple[int, int]:
    try:
        if isinstance(config_value, list) and len(config_value) == 2 and all(isinstance(p, int) for p in config_value): return tuple(config_value) # type: ignore
    except: pass
    return default

# --- HELPER for Inline Markup ---
def process_inline_markup(text_content: str, base_style: str, styles: Dict[str, str], compiled_rules: Dict[str, Optional[re.Pattern]]) -> Text:
    output_text = Text("", style=base_style)
    inline_rule_map = { # Map named group from regex to the style NAME
        "code": styles.get("style_inline_code", "default"),
        "bold_star": styles.get("style_inline_bold", "bold"),
        "bold_under": styles.get("style_inline_bold", "bold"),
        "italic_star": styles.get("style_inline_italic", "italic"),
        "italic_under": styles.get("style_inline_italic", "italic"),
    }
    inline_patterns = [ # Get compiled patterns using keys from DETECTIONS
        compiled_rules.get("inline_code"),
        compiled_rules.get("inline_bold_star"), compiled_rules.get("inline_bold_under"),
        compiled_rules.get("inline_italic_star"), compiled_rules.get("inline_italic_under"),
    ]
    valid_inline_patterns = [p for p in inline_patterns if p]
    if not valid_inline_patterns:
        output_text.append(text_content); return output_text

    combined_pattern = "|".join(p.pattern for p in valid_inline_patterns)
    try:
        finder_re = re.compile(combined_pattern)
    except re.error as e:
        print(f"ERROR: Invalid combined inline regex for finditer: {e}", file=sys.stderr)
        output_text.append(text_content); return output_text # Fallback

    last_end = 0
    for match in finder_re.finditer(text_content):
        start, end = match.span()
        match_group_name = match.lastgroup # Name of group (e.g., 'bold_star')

        if start > last_end: # Append text before match
            plain_bit = text_content[last_end:start]
            if plain_bit: # Ensure it's not empty
                 output_text.append(plain_bit)

        # --- Process the matched markup ---
        content = None # Reset content for each match
        if match_group_name and match_group_name in inline_rule_map:
            # MODIFICATION: Extract content using specific named group 'content_rulename'
            # Construct the expected content group name (e.g., content_bold_star)
            content_group_name = f"content_{match_group_name}"
            try:
                content = match.group(content_group_name)
            except IndexError: # This happens if the named group doesn't exist in the match
                print(f"Warning: Could not extract content group '{content_group_name}' from inline match for '{match_group_name}'. Regex or group name mismatch?", file=sys.stderr)
                content = None # Ensure content is None if extraction fails

            # --- ADDED CHECK FOR NONE CONTENT ---
            if content is not None:
                style_str = inline_rule_map[match_group_name]
                try:
                    # Combine base style with specific inline style
                    parsed_base_style = Style.parse(base_style)
                    parsed_inline_style = Style.parse(style_str)
                    # Handle attribute-only styles correctly (bold, italic)
                    if style_str == "bold" or style_str == "italic":
                       # Apply only the attribute, keep base color etc.
                       combined_style = parsed_base_style + parsed_inline_style
                    else:
                        # For styles with color/bg, let the inline style override fully if needed,
                        # but Rich's Style.combine often handles this well.
                       combined_style = Style.combine([parsed_base_style, parsed_inline_style])

                    output_text.append(content, style=combined_style)
                except StyleSyntaxError as e_style:
                     print(f"ERROR: Invalid style '{style_str}' or '{base_style}' for inline {match_group_name}: {e_style}", file=sys.stderr)
                     output_text.append(content, style=base_style) # Fallback append
                except Exception as e_combine:
                     print(f"ERROR: processing inline part '{content}' for {match_group_name}: {e_combine}", file=sys.stderr)
                     output_text.append(content, style=base_style) # Fallback append
            else:
                # If content IS None (e.g., empty bold **), append the raw match or nothing?
                # Let's append the raw matched string with base style as a safe fallback.
                raw_match_text = match.group(0)
                if raw_match_text:
                    output_text.append(raw_match_text)
                # Optional: Print warning only if raw_match_text was expected but content was None
                # if raw_match_text != match.group(0): # Heuristic check
                #    print(f"Warning: Extracted 'None' content for inline match '{match_group_name}'. Appending raw: '{raw_match_text}'", file=sys.stderr)


        else:
            # Match found by combined regex, but couldn't identify group? Append raw.
             raw_match_text = match.group(0)
             if raw_match_text:
                 output_text.append(raw_match_text)

        last_end = end

    # 3. Append any remaining plain text after the last match
    if last_end < len(text_content):
        remaining_bit = text_content[last_end:]
        if remaining_bit: # Ensure not empty
             output_text.append(remaining_bit)

    return output_text
# ==============================================================================
# 5. Main Styling Logic
# ==============================================================================
def apply_styles(
    text_content: str,
    compiled_rules: Dict[str, Optional[re.Pattern]],
    style_mapping: Dict,
    styles: Dict,
    console: Console,
    debug: bool = False,
    keep_markup: bool = False
):
    renderables: List = []
    in_code_block = False; code_block_content: List[str] = []; code_block_language: str = ""
    code_block_config: Dict = style_mapping.get("code_block", {})
    in_blockquote = False; blockquote_content: List[str] = []
    blockquote_config: Dict = style_mapping.get("blockquote", {})
    in_list_block = False; current_tree: Optional[Tree] = None
    node_stack: List[Tuple[int, Any]] = []
    list_block_config: Dict = style_mapping.get("list_block", {})
    list_guide_style_name = list_block_config.get("guide_style", "")
    list_guide_style = styles.get(list_guide_style_name, "default") # Use loaded style
    indent_width = 2; max_list_levels_styled = 10
    default_style_name = style_mapping.get("default_text", "style_default")
    default_style = styles.get(default_style_name, "default") # Use loaded style
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

    # --- Correctly Indented Helpers ---
    def finalize_tree():
        nonlocal in_list_block, current_tree, node_stack
        if current_tree:
            renderables.append(current_tree)
        in_list_block = False
        current_tree = None
        node_stack = []

    def finalize_blockquote():
        nonlocal in_blockquote, blockquote_content
        if blockquote_content:
            panel_border_style_name=blockquote_config.get("panel_border_style", "default")
            content_style_name=blockquote_config.get("content_style", "default")
            panel_padding_config=blockquote_config.get("panel_padding")
            panel_border_style=styles.get(panel_border_style_name, "default") # Use loaded style
            content_style_str=styles.get(content_style_name, "default") # Use loaded style
            panel_padding=get_panel_padding(panel_padding_config)
            quote_str="\n".join(blockquote_content)
            try:
                # Process inline markup within the blockquote content
                quote_text = process_inline_markup(quote_str, content_style_str, styles, compiled_rules)
            except Exception as e:
                if debug: print(f"DEBUG Warning: Error processing inline in blockquote: {e}", file=sys.stderr)
                quote_text = Text(quote_str, style=content_style_str) # Fallback to raw text

            panel = Panel(quote_text, border_style=panel_border_style, padding=panel_padding)
            renderables.append(panel)
        # Reset state regardless of content
        in_blockquote = False
        blockquote_content = []

    def finalize_code_block():
        nonlocal in_code_block, code_block_content, code_block_language
        if code_block_content:
            panel_border_style_name=code_block_config.get("panel_border_style", "default")
            panel_title_style_name=code_block_config.get("panel_title_style", "default")
            syntax_theme=code_block_config.get("syntax_theme", "default")
            panel_padding_config=code_block_config.get("panel_padding")
            panel_border_style=styles.get(panel_border_style_name, "default") # Use loaded style
            panel_title_style=styles.get(panel_title_style_name, "default") # Use loaded style
            panel_padding=get_panel_padding(panel_padding_config)
            code_str="\n".join(code_block_content)
            renderable_content: object
            can_highlight = False
            if pygments and code_block_language and code_block_language != "default":
                try:
                    get_lexer_by_name(code_block_language)
                    can_highlight = True
                except ClassNotFound:
                     if debug: print(f"DEBUG Warning: Pygments lexer not found for '{code_block_language}'.", file=sys.stderr)
                except Exception as e:
                     if debug: print(f"DEBUG Warning: Pygments error for '{code_block_language}': {e}.", file=sys.stderr)

            if can_highlight:
                renderable_content = Syntax(code_str, code_block_language, theme=syntax_theme, line_numbers=False, word_wrap=False, background_color="default", dedent=False)
            else:
                # Use default style for non-highlighted code text
                renderable_content = Text(code_str, style=styles.get("style_default", "default"))

            panel = Panel(renderable_content, title=code_block_language if code_block_language != "default" else None, title_align="left", border_style=panel_border_style, padding=panel_padding)
            if panel.title:
                try:
                    panel.title = Text(str(panel.title), style=Style.parse(panel_title_style))
                except StyleSyntaxError:
                    panel.title = Text(str(panel.title), style="default") # Fallback title style
            renderables.append(panel)
        # Reset state regardless of content
        in_code_block = False
        code_block_content = []
        code_block_language = ""

    # 5.5. Line-by-Line Processing Loop
    for i, line in enumerate(lines):
        # 5.5.1. Code Blocks
        fence_match = code_fence_rule.match(line) if code_fence_rule else None
        if fence_match:
            if in_list_block: finalize_tree()
            if in_blockquote: finalize_blockquote()
            if not in_code_block:
                in_code_block = True
                code_block_language = fence_match.group(1) if len(fence_match.groups()) >= 1 else ""
                code_block_language = code_block_language or "default"
                code_block_content = []
                continue
            else:
                finalize_code_block()
                continue
        if in_code_block:
            code_block_content.append(line)
            continue

        # 5.5.2. Blockquotes
        is_blockquote_line = blockquote_rule.match(line) if blockquote_rule else None
        if is_blockquote_line:
            if in_list_block: finalize_tree()
            if not in_blockquote:
                in_blockquote = True
                blockquote_content = []
            # Strip the ">" prefix before adding
            quote_line_content = re.sub(r"^\s*>\s?", "", line)
            blockquote_content.append(quote_line_content)
            continue
        elif in_blockquote:
             finalize_blockquote() # Finalize if current line is NOT a quote line

        # 5.5.3. List Trees
        list_match = None; is_bullet = False
        if list_bullet_rule and (match := list_bullet_rule.match(line)): list_match = match; is_bullet = True;
        if not list_match and list_numbered_rule and (match := list_numbered_rule.match(line)): list_match = match; is_bullet = False;

        if list_match:
            # Make sure to finalize other blocks if starting a list
            if in_blockquote: finalize_blockquote() # Should be handled above, but defensive check
            # --- List Processing Logic ---
            base_style_key = "list_item_bullet" if is_bullet else "list_item_numbered"; base_style_name = style_mapping.get(base_style_key)
            if base_style_name and isinstance(base_style_name, str) and len(list_match.groups()) >= 2:
                indent_str = list_match.group(1); content_str = list_match.group(2); current_level = get_indent_level(indent_str + (" " if is_bullet else "  "), indent_width)

                if not in_list_block: # Starting a new list block
                    in_list_block = True
                    current_tree = Tree("", guide_style=list_guide_style)
                    node_stack = [(-1, current_tree)] # Add root node at level -1

                # Find the correct parent node based on indentation level
                while node_stack and node_stack[-1][0] >= current_level:
                    node_stack.pop()

                if not node_stack: # Error condition: popped too much?
                    if debug: print(f"DEBUG Warning: List parsing error - node stack empty for line: {line}", file=sys.stderr);
                    finalize_tree(); # Reset state and treat as default line
                    # Fall through to default handling below this 'if list_match' block
                else:
                    # Add to the parent node found
                    parent_level, parent_node = node_stack[-1]
                    # Determine the style for this level
                    level0_style = styles.get(f"{base_style_name}0", default_style)
                    level_idx = current_level % max_list_levels_styled
                    style_name = f"{base_style_name}{level_idx}"
                    content_style_str = styles.get(style_name, level0_style) # Use loaded style

                    try:
                        node_label: Text
                        text_to_process = ""
                        if keep_markup:
                            list_prefix = ""
                            try:
                                # Find prefix reliably
                                marker_pos = line.find(content_str)
                                if marker_pos != -1:
                                   list_prefix = line[:marker_pos].lstrip(" ") # Get text between indent and content
                                else:
                                   list_prefix = ("* " if is_bullet else "1. ") # Fallback prefix
                            except ValueError:
                                list_prefix = ("* " if is_bullet else "1. ") # Fallback prefix
                            text_to_process = indent_str + list_prefix + content_str
                        else:
                             text_to_process = content_str # Just use content if not keeping markup

                        # Process inline markup for the list item content
                        node_label = process_inline_markup(text_to_process, content_style_str, styles, compiled_rules)

                        # Add the new node to the tree
                        new_node = parent_node.add(node_label)
                        node_stack.append((current_level, new_node))
                        # Line successfully handled as a list item
                        continue # Go to next line immediately
                    except Exception as e:
                        print(f"ERROR: Adding node to tree for line '{line}': {e}", file=sys.stderr)
                        traceback.print_exc(file=sys.stderr) # More detail on error
                        finalize_tree() # Reset state and fall through
            else: # Regex matched but invalid mapping or groups
                 if debug: print(f"DEBUG Warning: List regex matched but groups/mapping invalid: {line[:50]}...", file=sys.stderr)
                 if in_list_block: finalize_tree(); # Finalize list if it was open
                 # Fall through to default handling
        elif in_list_block: # Current line is not a list item, finalize previous block
             finalize_tree()


        # 5.5.4. Handle Non-Block, Non-List Lines (Headers, HR, etc.)
        matched_line = False # Reset match flag for each line

        # Check Headers
        header_match_handled = False
        if header_numbered_rule and (match := header_numbered_rule.match(line)):
            style_name = style_mapping.get("header_numbered"); style_str = styles.get(style_name, default_style)
            text_to_process = line if keep_markup else f"{match.group(1)}. {match.group(2)}"
            renderables.append(process_inline_markup(text_to_process, style_str, styles, compiled_rules)); matched_line = True; header_match_handled = True
        elif header1_rule and (match := header1_rule.match(line)):
            style_name = style_mapping.get("header1"); style_str = styles.get(style_name, default_style)
            text_to_process = line if keep_markup else match.group(1)
            renderables.append(process_inline_markup(text_to_process, style_str, styles, compiled_rules)); matched_line = True; header_match_handled = True
        elif header2_rule and (match := header2_rule.match(line)):
             style_name = style_mapping.get("header2"); style_str = styles.get(style_name, default_style)
             text_to_process = line if keep_markup else match.group(1)
             renderables.append(process_inline_markup(text_to_process, style_str, styles, compiled_rules)); matched_line = True; header_match_handled = True
        elif header3_rule and (match := header3_rule.match(line)):
             style_name = style_mapping.get("header3"); style_str = styles.get(style_name, default_style)
             text_to_process = line if keep_markup else match.group(1)
             renderables.append(process_inline_markup(text_to_process, style_str, styles, compiled_rules)); matched_line = True; header_match_handled = True

        # Check Horizontal Rule (only if not already matched as header)
        if not header_match_handled and hr_rule and hr_rule.match(line):
            hr_style_name = style_mapping.get("horizontal_rule", "default"); hr_style = styles.get(hr_style_name, "default"); renderables.append(Rule(style=hr_style)); matched_line = True;

        # Check Other Generic Line Rules (only if not matched above)
        if not matched_line:
             # Define rules to skip in this generic loop more robustly
             skipped_rules = {
                 "code_block_fence", "blockquote_start", "list_item_bullet", "list_item_numbered",
                 "header_numbered", "header1", "header2", "header3", "horizontal_rule",
                 "inline_bold_star", "inline_bold_under", "inline_italic_star", "inline_italic_under", "inline_code"
             }
             for name, pattern in compiled_rules.items():
                 if name in skipped_rules or pattern is None: continue;
                 match = pattern.match(line)
                 if match:
                     mapping_value = style_mapping.get(name)
                     if isinstance(mapping_value, str) and (style_str := styles.get(mapping_value)):
                          renderables.append(process_inline_markup(line, style_str, styles, compiled_rules)); matched_line = True; break; # Break after first match
                     else:
                         if debug: print(f"DEBUG Warning: Rule '{name}' matched but no valid style mapping found.", file=sys.stderr)
                         # Decide: Fall through to default or handle explicitly? Let's fall through.

        # 5.5.5. Default Fallback Handler
        if not matched_line:
             # Apply default style and process inline markup for any remaining lines
             renderables.append(process_inline_markup(line, default_style, styles, compiled_rules))

    # 5.6. End of Input Finalization (handle blocks that might be open)
    if in_list_block: finalize_tree();
    if in_blockquote:
        # This shouldn't happen with correct logic, but as a safeguard
        if debug: print("DEBUG Warning: Input ended unexpectedly inside blockquote.", file=sys.stderr);
        finalize_blockquote();
    if in_code_block:
        # This is common if the closing fence ``` is missing
        if debug: print("DEBUG Warning: Input ended unexpectedly inside code block (missing closing fence?).", file=sys.stderr);
        finalize_code_block();

    # 5.7. Print All Renderables
    for item in renderables:
        console.print(item)

# ==============================================================================
# 6. Main Execution Block
# ==============================================================================
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
        help="Filename of the style definitions JSON file (e.g., 'styles.json', 'calm-styles.json') within the config directory."
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

    # Check if input is from TTY (likely interactive use without pipe)
    if sys.stdin.isatty() and not args.debug: # Allow debug mode even with TTY for config testing
        parser.print_usage(file=sys.stderr)
        print("Error: Input must be piped from another command.", file=sys.stderr)
        print("Example: llm 'prompt' | llm-style.py", file=sys.stderr)
        sys.exit(1)

    # Load configurations using the specified style file
    try:
        compiled_rules, style_mapping, styles = load_all_configs(
            args.config_dir,
            args.style, # Pass the style filename
            debug=args.debug
        )
    except SystemExit: # Handle exits from config loading/validation
        sys.exit(1)
    except Exception as e:
        print(f"FATAL: Unexpected error loading/validating configuration: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    # Read input from stdin
    try:
        input_text = sys.stdin.read()
    except Exception as e:
        print(f"Error reading standard input: {e}", file=sys.stderr)
        sys.exit(1)

    # Apply styles and print
    console = Console()
    try:
        apply_styles(
            input_text,
            compiled_rules,
            style_mapping,
            styles,
            console,
            debug=args.debug,
            keep_markup=args.keep_markup
        )
    except Exception as e:
        # Catch unexpected errors during the styling process
        print(f"\n--- Unexpected Error During Styling ---", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        print(f"This might indicate an issue with the input text structure or a bug in the styling logic.", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        # Optionally print raw input for debugging
        # print(f"\n--- Raw Input Trace: ---", file=sys.stderr)
        # print(input_text, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()