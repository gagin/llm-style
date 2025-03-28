.. epigraph::

   Colors are perception, child. We decide what they mean.

   -- Inspired by themes in Brandon Sanderson's *Warbreaker*

================================================
llm-style: Rich Terminal Styling for LLM Output
================================================

**Version: 0.6.0**

Rich terminal styling for Markdown-like LLM output using panels, trees, inline styles, dynamic color transformations, and configurable regex rules.

.. figure:: /path/to/screenshot.png
   :alt: Screenshot showing styled LLM output

   *(Add a screenshot here showing an example of styled output. Note: GitHub may not render this figure directive correctly.)*


Motivation
----------

Raw text output from LLMs can be hard to read, especially when it contains structural elements like headers, lists, or code blocks but isn't always perfectly valid Markdown. Standard Markdown renderers might fail or produce suboptimal results on this "Markdown-like" text.

``llm-style`` aims to bridge this gap by using a combination of configurable regular expressions and a state machine to detect common structural elements and apply rich formatting (colors, bold, italic, panels, tree guides) using the excellent ``rich`` Python library, making the output significantly more readable directly in the terminal.

Key Features
------------

*   **Markdown-like Aware:** Designed to handle common structures found in LLM output, even if not strictly valid Markdown.
*   **Highly Configurable:** Uses simple JSON files for:
    *   `detection.json`: Define regex patterns to identify structures.
    *   `mapping.json`: Map detected structures to style names or block configurations.
    *   `<style-file>.json` (e.g., `styles.json`, `calm-styles.json`): Define named styles using ``rich``'s powerful syntax, including dynamic transformations.
*   **Rich Output:** Leverages the ``rich`` library for:
    *   Colors (Truecolor, 256, basic).
    *   Styles (bold, italic, underline, dim, reverse, etc.).
    *   Panel borders around code blocks and blockquotes.
    *   Tree guide lines for nested lists.
    *   Syntax highlighting for code blocks (requires ``pygments``).
*   **Dynamic Inline Styles:** Configure inline styles (like bold) to dynamically adjust color (brightness, saturation, hue) based on the surrounding text's color.
*   **Style Themes:** Load different style definitions using the ``--style`` argument.
*   **Flexible Detection:** Uses regex for primary structure detection, allowing custom rules beyond standard Markdown.
*   **Pipeline Friendly:** Designed to be used in standard Unix pipelines (e.g., ``llm ... | llm-style.py``).
*   **Shell Integration:** Optional shell function (Zsh example provided) to automatically pipe `llm` output.
*   **Debug Mode:** Includes a ``--debug`` flag for verbose configuration loading/validation and transformation output.
*   **Markup Preservation:** Optional ``--keep-markup`` flag to display original block markup characters (``#``, ``*``, ``**``).


Installation
------------

1.  **Prerequisites:**
    *   Python 3.7+ (May need 3.8+ for full `colorsys` support if not built-in)
    *   `pip` (Python package installer)

2.  **Required Libraries:**
    *   `rich`: The core rendering library. (Version 13+ recommended).
    *   `pygments` (Optional, but Recommended): For syntax highlighting within code blocks.
    *   `colorsys` (Usually built-in with Python): Required for dynamic color transformations. If missing, transforms will be skipped.

    Install them using pip:

    .. code-block:: bash

        pip install "rich>=13.0" pygments

3.  **Get the Script:**
    *   Clone this repository or download the `llm-style.py` script directly.

        .. code-block:: bash

            # Example if cloning
            git clone https://github.com/gagin/llm-style.git
            cd llm-style

4.  **Make Executable (Optional):**

    .. code-block:: bash

        chmod +x llm-style.py


Usage
-----

``llm-style`` reads text from standard input and prints styled output to standard output. It's designed to be used in a pipeline.

**Basic Usage (Default Style):**

Pipe the output of the ``llm`` command (or any text-producing command) into the script. This uses ``styles.json`` in your config directory (or creates a default one based on the script's internal green theme).

.. code-block:: bash

    llm "Explain Python decorators" | python llm-style.py
    # Or if executable:
    # llm "Explain Python decorators" | ./llm-style.py

**Using a Specific Style Theme:**

Use the ``--style`` argument to specify a different JSON file containing style definitions from your config directory.

.. code-block:: bash

    # Assuming you have ~/.config/llm-style/tan-crazybold-style.json
    llm "Pros and cons" | python llm-style.py --style tan-crazybold-style.json

**Using Shell Integration (Recommended for Convenience):**

If you've added the provided Zsh function (see "Shell Integration" section) to your ``.zshrc``, you can just use the ``llm`` command directly, and it will automatically be styled using your configured preference:

.. code-block:: bash

    # Assumes the 'llm' function is defined in .zshrc to pipe through the styler
    llm "This output will be automatically styled"

**Keeping Block Markup:**

.. code-block:: bash

    llm "Show raw markdown" | python llm-style.py --keep-markup

**Debugging Configuration:**

.. code-block:: bash

    llm "Debug this" | python llm-style.py --debug --style my-debug-style.json > /dev/null 2> debug.log

*(Note: Replace ``python llm-style.py`` with ``./llm-style.py`` if executable and in the correct path/directory).*


Comparison with Other Tools
---------------------------

Tools like `glow`_, `mdcat`_, and `bat`_ are excellent terminal Markdown renderers/viewers. Why use ``llm-style``?

*   **Strictness:** Tools like ``glow`` or ``mdcat`` often expect reasonably valid CommonMark or GitHub Flavored Markdown. They might produce errors or poor formatting if the LLM output deviates significantly (e.g., inconsistent indentation, malformed lists, unusual syntax). ``llm-style`` uses regex and is designed to be more forgiving of "Markdown-like" text.
*   **Flexibility vs. Robustness:** Standard Markdown renderers have robust parsers for *Markdown*, handling complex nesting and edge cases correctly, including inline formatting. ``llm-style``'s regex-based approach (especially for inline elements) is less robust for pure Markdown but offers the flexibility to style arbitrary, non-Markdown patterns defined in ``detection.json``.
*   **Unique Rendering:** ``llm-style`` leverages ``rich`` features not typically found in standard Markdown viewers:
    *   **Panels:** Draws borders around code blocks and blockquotes.
    *   **Trees:** Draws guide lines for nested lists.
*   **Configuration:** ``llm-style`` offers direct JSON configuration for detection patterns, style mapping, and `rich` styles, including dynamic transformations.

**Choose ``llm-style`` if:**

*   Your input is often "Markdown-like" but not strictly valid.
*   You want the specific visual structure provided by Panels and Trees.
*   You need to style custom text patterns beyond standard Markdown using regex.
*   You want dynamic inline styling based on context.
*   You prefer direct JSON configuration tied to ``rich`` and want theme support.

**Choose standard tools (``glow``, ``bat``, ``mdcat``) if:**

*   Your input is reliably well-formed Markdown.
*   Robust handling of all Markdown features (especially complex inline/nested elements) is the top priority.
*   You prefer using existing theme ecosystems (e.g., for ``bat``).

.. _glow: https://github.com/charmbracelet/glow
.. _mdcat: https://github.com/swsnr/mdcat
.. _bat: https://github.com/sharkdp/bat


Configuration
-------------

On the first run, if the configuration directory (default: ``~/.config/llm-style/``) or the default config files don't exist, ``llm-style`` will create them with default settings (based on a greenish theme).

*   **`detection.json`:** Maps rule names to Python regex patterns for structure detection.
*   **`mapping.json`:** Connects rule names from `detection.json` to style names or special block configurations (like panels). Requires ``"default_text"``.
*   **`<style-file>.json`** (e.g., `styles.json`, specified via ``--style``): Maps style names (referenced in `mapping.json`) to ``rich`` style definitions. This is where colors, attributes, and dynamic transformations are defined.

**Recommendation:** Copy the default `styles.json` generated by the script or provided theme examples (like `tan-crazybold-style.json`) from the source repository into your `~/.config/llm-style/` directory. Use these as starting points for your own customization by editing the JSON files.


Color Guide (Using `rich` Styles)
---------------------------------

The styles defined in your style JSON file use the syntax understood by the `rich`_ library.

**How to Specify Colors:**

1.  **Standard Color Names:** Use common names like ``"red"``, ``"green"``, ``"blue"``, ``"yellow"``, ``"magenta"``, ``"cyan"``, ``"white"``, ``"black"``, and other W3C names like ``"tan"``, ``"wheat"``, ``"lightblue"``, ``"purple"``. Hex codes are generally more reliable than less common names.
2.  **Hex Codes (Truecolor):** For terminals supporting Truecolor (most modern ones), use CSS-style hex codes. Example: ``"#FFA500"`` (Orange), ``"#A0522D"`` (Sienna).
3.  **RGB Tuples (Truecolor):** Specify RGB values from 0-255. Example: ``"rgb(255,165,0)"``.
4.  **Numbered Colors (256-Color Terminals):** Use numbers 0-255. Example: ``"color(178)"`` (Gold/Orange).

**Combining with Attributes:**

Combine colors with attributes like ``bold``, ``italic``, ``underline``, ``dim``, ``strike``, ``reverse``, and background colors using ``on <color>``.

*Example:* ``"style_error": "bold white on red"``
*Example:* ``"style_inline_bold": "bold reverse"``

Refer to the `rich Style documentation`_ for comprehensive details.

.. _rich: https://github.com/Textualize/rich
.. _rich Style documentation: https://rich.readthedocs.io/en/latest/style.html


Inline Style Customization & Transformations
------------------------------------------

Inline styles (`bold`, `italic`, `code`) are handled via rules like `inline_bold_star`, `inline_code`, etc., in `detection.json`. These implicitly map to styles named `style_inline_bold`, `style_inline_italic`, and `style_inline_code` in your active style JSON file.

You can define these styles in two ways:

1.  **Simple String:** Uses standard `rich` style syntax. The style is applied directly. If only an attribute (like `italic`) is given, the color is inherited from the surrounding text.

    .. code-block:: json

        {
          "style_inline_italic": "italic",
          "style_inline_code": "yellow on grey19",
          "style_inline_bold": "bold reverse"
        }

2.  **Object with Transformation:** Allows dynamic color adjustment based on the surrounding text's color. Requires the `colorsys` Python module.

    .. code-block:: json

        {
          "style_inline_bold": {
            "attributes": "bold",
            "transform": {
              "adjust_brightness": 1.25,
              "adjust_saturation": 1.1,
              "shift_hue": 5
            }
          }
        }

    *   `"attributes"`: (String) Basic `rich` style attributes (e.g., `"bold"`, `"bold underline"`).
    *   `"transform"`: (Object, Optional) Rules for color modification:
        *   `"adjust_brightness"`: (Float) Multiplier for brightness (HSL Lightness). `1.0` = no change, `1.2` = 20% brighter, `0.8` = 20% dimmer. Values significantly > 1.0 may clip towards white.
        *   `"adjust_saturation"`: (Float) Multiplier for saturation (HSL Saturation). `1.0` = no change, `1.2` = 20% more saturated, `0.8` = 20% less saturated (more grey).
        *   `"shift_hue"`: (Float) Degrees to shift hue on the color wheel (0-360). Positive values shift typically towards red/orange/yellow, negative towards purple/blue/cyan (depends on start hue).

    **How it works:** The script gets the color of the text surrounding the inline element (the "base color"). If a `transform` object is defined, it attempts to convert the base color to RGB, then to HSL, applies the adjustments, converts back to RGB, and uses this *new* color along with the defined `attributes`. If the base color cannot be reliably converted to RGB (e.g., "default" or system colors), the transformation is skipped, and only the defined `attributes` are applied (inheriting the base color). See the note below regarding potential issues.


A Note on Color Transformations and `rich` / Environment Issues
-------------------------------------------------------------

The dynamic color transformation feature relies on:
1. The `colorsys` standard Python library module.
2. The ability to reliably get an RGB representation of the "base color" from the `rich.color.Color` object provided by the parsed base style.

During development, peculiar `AttributeError`s related to `rich.color.ColorType.RGB` and `rich.color.ColorType.SYSTEM` were encountered, even when using recent versions of `rich` (e.g., 13.9.x) in certain environments (specifically observed within a Conda setup). This occurred despite these attributes being present in the library's source code and documentation. The root cause likely relates to environment inconsistencies or how Python modules are loaded/shadowed.

**The Workaround:** The `_apply_transform` function in `llm-style.py` includes a workaround that avoids directly referencing `ColorType.RGB` or `ColorType.SYSTEM` attributes by name. Instead, it checks the integer value of the color type (`int(base_color.type)`) against expected standard values (e.g., `3` for `TRUECOLOR`, `0` for `DEFAULT`, `1` for `SYSTEM`) or accesses the `.triplet` attribute directly when the type is known to be `TRUECOLOR`. It also includes error handling in case `get_truecolor()` fails internally due to related issues.

**Caveats:**
*   This workaround relies on the internal integer values of `ColorType` members remaining consistent with standard `rich` versions. Significant changes in `rich`'s internal enum structure could break this workaround.
*   Transformations may still fail if `get_truecolor()` cannot resolve certain base colors (like `STANDARD` names or complex definitions) to RGB.
*   If you encounter persistent issues with transformations failing (check `--debug` output, look for warnings about failing to get RGB or apply transforms), the most robust solution is often to ensure a clean Python environment (e.g., a fresh virtual environment or Conda environment) with a cleanly installed `rich` library (`pip install --force-reinstall "rich>=13.0"`).


Shell Integration (Optional)
----------------------------

For convenience, you can add a function to your shell's configuration file (e.g., `.zshrc` for Zsh, `.bashrc` for Bash) to automatically pipe the output of the `llm` command through the styler.

**Example for `.zshrc`:**

This function overrides the default `llm` command.

.. code-block:: zsh

    # ------------------------------------------------------------
    # llm-style integration (Override llm command)
    # ------------------------------------------------------------

    # --- Configure these paths/filenames ---
    _LLM_STYLE_SCRIPT_PATH="/path/to/your/llm-style.py" # EDIT THIS: Absolute path to the script
    _LLM_STYLE_DEFAULT_FILE="styles.json"             # EDIT THIS: Filename of your preferred default style
    # ----------------------------------------

    llm() {
      # Use 'command llm' to call the *original* llm executable, preventing recursion
      if ! command -v llm &> /dev/null; then
        echo "Zsh Error: Original 'llm' command not found." >&2
        return 1
      fi

      # Check if style script exists and is runnable
      # Use -f to check if it's a regular file and -r for readable OR -x for executable
      if [[ ! -f "$_LLM_STYLE_SCRIPT_PATH" || (! -r "$_LLM_STYLE_SCRIPT_PATH" && ! -x "$_LLM_STYLE_SCRIPT_PATH") ]]; then
         echo "Zsh Warning: llm-style script not found or not readable/executable at '$_LLM_STYLE_SCRIPT_PATH'. Running 'llm' without styling." >&2
         command llm "$@" # Run original llm directly as fallback
         return $?
      fi

      # Run the original llm and pipe to the style script with the chosen style
      # Ensure python executable is correct (e.g., python3 or just python)
      command llm "$@" | python "$_LLM_STYLE_SCRIPT_PATH" --style "$_LLM_STYLE_DEFAULT_FILE"
      # Preserve the exit status of the pipe (Zsh specific: index 2 is the python script)
      return ${pipestatus[2]}
    }

    # ------------------------------------------------------------
    # End llm-style integration
    # ------------------------------------------------------------

**Setup:**
1.  **Edit** the function above, setting `_LLM_STYLE_SCRIPT_PATH` to the correct absolute path of your `llm-style.py` script.
2.  **Set** `_LLM_STYLE_DEFAULT_FILE` to the filename (within your `~/.config/llm-style/` directory) of the style theme you want to use by default (e.g., `"styles.json"`, `"tan-crazybold-style.json"`).
3.  **Add** the edited function block to your `~/.zshrc` file.
4.  **Reload** your shell configuration (`source ~/.zshrc` or open a new terminal).

Now, running `llm "your prompt"` will automatically apply the styling using your chosen default style file.

**Bypassing the Wrapper:** To run the original `llm` command without styling, use:
   ``command llm "your prompt"``
   or
   ``\llm "your prompt"``


GitHub Rendering Note
---------------------

Please be aware that GitHub's rendering of reStructuredText (`.rst`) files has known limitations compared to standard tools like Sphinx or the output generated by this script in your terminal. Complex nested lists or certain directives (like `.. figure::` or `.. epigraph::`) might not display as intended on GitHub.

**For the best rendering experience *on GitHub*, consider converting this README to Markdown (`README.md`).**


Limitations
-----------

*   **Inline Parsing:** The current inline parsing (for bold, italic, code) uses regex and is basic. It may not correctly handle complex nesting or edge cases found in full Markdown implementations (e.g., bold inside italic within a link).
*   **Regex Dependency:** The quality of the output heavily depends on the accuracy and comprehensiveness of the regex patterns in `detection.json`. Poorly written regexes can lead to misidentified structures.
*   **Block State Machine:** The logic for handling code blocks, blockquotes, and lists is relatively simple and might break on complex, interleaved, or malformed structures.
*   **Color Transformation Robustness:** Dynamic color transformation depends on reliably getting RGB values and may fail for certain base color types or due to environment issues (see note above).
*   **Performance:** While generally performant for typical LLM output sizes, extremely large inputs might experience slower processing due to the regex and line-by-line state management.


Future Development
------------------

*   **Testing:** Implement a robust test suite, particularly focusing on edge cases, different transformation inputs, and "weird" text inputs to improve parsing robustness.
*   **`llm` Plugin:** Develop an official plugin for Simon Willison's ``llm`` tool for seamless integration (e.g., ``llm ... --format=llm-style``).
*   **Enhanced Inline Parsing:** Investigate more robust methods for handling inline markup, potentially using a more advanced regex approach or a limited custom parser (balancing flexibility with complexity).
*   **Configuration Options:**
    *   Make list indentation width configurable.
    *   Allow customization of Tree guide characters.
    *   Expose more Panel options (padding, title alignment) via `mapping.json`.
*   **More Structure Detection:** Add rules and logic to detect and style other common elements like tables or definition lists if feasible with the line-based approach.
*   **Performance Profiling:** Analyze performance on large inputs and optimize if necessary.
*   **Documentation:** Improve documentation for creating custom configurations, especially around style transformations and troubleshooting.


Contributing
------------

Contributions, issues, and feature requests are welcome! Please check the GitHub repository issues section at https://github.com/gagin/llm-style/issues.


Credits
-------

This script was implemented by Google Gemini 2.5 Pro (Experimental Model 03-25), ideated, curated and iterated by the author, Alex Gaggin.


License
-------

MIT License

Copyright (c) 2025 Alex Gaggin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.