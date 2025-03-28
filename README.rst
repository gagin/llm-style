.. epigraph::

   Colors are perception, child. We decide what they mean.

   -- Inspired by themes in Brandon Sanderson's *Warbreaker*

================================================
llm-style: Rich Terminal Styling for LLM Output
================================================

**Version: 0.6.0**

Rich terminal styling for Markdown-like LLM output using panels, trees, inline styles, dynamic color transformations, and configurable regex rules.

.. figure:: example.png
   :alt: Screenshot showing styled LLM output (tan-crazybold-style.json)

   *(Above: Example using the ``tan-crazybold-style.json`` theme. The "crazy" reverse video for bold is intentional for high contrast.)*


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
    *   `<style-file>.json` (e.g., `styles.json`, `green-theme.json`): Define named styles using `rich`'s powerful syntax, including dynamic transformations.
*   **Rich Output:** Leverages the ``rich`` library for:
    *   Colors (Truecolor, 256, basic).
    *   Styles (bold, italic, underline, dim, reverse, etc.).
    *   **Panels:** Draws borders around code blocks and blockquotes.
    *   **Trees:** Draws guide lines for nested lists.
    *   Syntax highlighting for code blocks (requires ``pygments``).
*   **Dynamic Inline Styles:** Configure inline styles (like bold) to dynamically adjust color (brightness, saturation, hue) based on the surrounding text's color.
*   **Style Themes:** Load different style definitions using the ``--style`` argument. The default is `styles.json`.
*   **Flexible Detection:** Uses regex for primary structure detection, allowing custom rules beyond standard Markdown.
*   **Pipeline Friendly:** Designed to be used in standard Unix pipelines (e.g., ``llm ... | llm-style.py``).
*   **Shell Integration:** Optional shell function (Zsh example provided) to automatically pipe `llm` output.
*   **Debug Mode:** Includes a ``--debug`` flag for verbose configuration loading/validation and transformation output.
*   **Markup Preservation:** Optional ``--keep-markup`` flag to display original block markup characters (`#`, `*`, `**`).


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

Pipe the output of the ``llm`` command (or any text-producing command) into the script. This uses `styles.json` in your config directory (by default `~/.config/llm-style/`), creating it with a default green theme if it doesn't exist.

.. code-block:: bash

    llm "Explain Python decorators" | python llm-style.py
    # Or if executable:
    # llm "Explain Python decorators" | ./llm-style.py

**Using a Specific Style Theme:**

Use the ``--style`` argument to specify a different JSON file located within your config directory.

.. code-block:: bash

    # Assuming you have ~/.config/llm-style/tan-crazybold-style.json
    llm "Pros and cons" | python llm-style.py --style tan-crazybold-style.json

**Using a Local Style File (without copying):**

You can use a style file from the current directory by setting the config directory to `.` *if* you also have `detection.json` and `mapping.json` present in the current directory (or you allow the script to create defaults there).

.. code-block:: bash

    # Assumes my-local-style.json, detection.json, mapping.json are in '.'
    llm "Use local style" | python llm-style.py --config-dir . --style my-local-style.json

**Using Shell Integration (Recommended for Convenience):**

If you've added the provided Zsh function (see "Shell Integration" section) to your ``.zshrc``, you can just use the ``llm`` command directly, and it will automatically be styled using your configured preference:

.. code-block:: bash

    # Assumes the 'llm' function is defined in .zshrc to pipe through the styler
    llm "This output will be automatically styled"

**Keeping Block Markup:**

.. code-block:: bash

    llm "Show raw markdown" | python llm-style.py --keep-markup

**Debugging Configuration:**

Redirect standard output to `/dev/null` and error/debug output to a file to isolate debug messages.

.. code-block:: bash

    llm "Debug this" | python llm-style.py --debug --style my-debug-style.json > /dev/null 2> debug.log

*(Note: Replace ``python llm-style.py`` with ``./llm-style.py`` if executable and in the correct path/directory).*

``--help`` Output
-----------------

.. code-block:: text

    usage: llm-style.py [-h] [--config-dir CONFIG_DIR] [--style STYLE] [--debug] [--keep-markup]

    Apply styles to text input based on configurable rules.

    options:
      -h, --help            show this help message and exit
      --config-dir CONFIG_DIR
                            Directory containing detection.json, mapping.json, and style JSON files. (default: ~/.config/llm-style)
      --style STYLE         Filename of the style definitions JSON file (e.g., 'styles.json', 'calm-styles.json') within the config directory. (default: styles.json)
      --debug               Enable debug/verbose output to stderr. (default: False)
      --keep-markup         Keep original Markdown block characters (e.g., '#', '*', '>') in the output. (default: False)


Comparison with Other Tools
---------------------------

*(This section remains largely the same - highlighting flexibility for "Markdown-like" text, unique rendering via Rich (Panels/Trees), and configuration)*

Tools like `glow`_, `mdcat`_, and `bat`_ are excellent terminal Markdown renderers/viewers. Why use ``llm-style``?

*   **Strictness:** Tools like `glow` or `mdcat` often expect reasonably valid CommonMark or GitHub Flavored Markdown... `llm-style` uses regex and is designed to be more forgiving...
*   **Flexibility vs. Robustness:** Standard Markdown renderers have robust parsers... `llm-style`'s regex-based approach... offers the flexibility to style arbitrary, non-Markdown patterns...
*   **Unique Rendering:** `llm-style` leverages ``rich`` features... Panels... Trees...
*   **Configuration:** `llm-style` offers direct JSON configuration... including dynamic transformations.

**Choose ``llm-style`` if:**

*   Your input is often "Markdown-like" but not strictly valid.
*   You want the specific visual structure provided by Panels and Trees.
*   You need to style custom text patterns beyond standard Markdown using regex.
*   You want dynamic inline styling based on context.
*   You prefer direct JSON configuration tied to ``rich`` and want theme support.

**Choose standard tools (``glow``, ``bat``, ``mdcat``) if:**

*   Your input is reliably well-formed Markdown.
*   Robust handling of all Markdown features... is the top priority.
*   You prefer using existing theme ecosystems...

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

1.  **Standard Color Names:** Use common names like ``"red"``, ``"green"``, ``"blue"``, ``"yellow"``, ``"magenta"``, ``"cyan"``, ``"white"``, ``"black"``. Hex codes are generally more reliable than less common names.
2.  **Hex Codes (Truecolor):** Recommended for specific colors if your terminal supports Truecolor. Example: ``"#FFA500"`` (Orange), ``"#A0522D"`` (Sienna).
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
    *   `"transform"`: (Object, Optional) Rules for color modification (`adjust_brightness`, `adjust_saturation`, `shift_hue`). See details in the source code or previous README versions if needed.

    **How it works:** The script gets the base color. If a `transform` object is defined, it attempts HSL adjustments and uses the *new* color with the defined `attributes`. If transformation fails (e.g., base color unusable), only `attributes` are applied.

**Important Note:** Inline styling (including transformations) is **not** applied within fenced code blocks (``` ```). The content of code blocks is treated literally to preserve code structure and syntax.


A Note on Color Transformations and `rich` / Environment Issues
-------------------------------------------------------------

*(This section remains largely the same - explains the dependency on `colorsys` and RGB conversion, the observed AttributeErrors, the integer-value workaround in the script, and recommends checking environment/reinstalling rich if issues persist)*

... The `_apply_transform` function in `llm-style.py` includes a workaround that avoids directly referencing `ColorType.RGB` or `ColorType.SYSTEM` attributes by name. Instead, it checks the integer value of the color type (`int(base_color.type)`)...

**Caveats:**
*   This workaround relies on internal integer values...
*   Transformations may still fail if `get_truecolor()` cannot resolve certain base colors...
*   If you encounter persistent issues... ensure a clean Python environment... (`pip install --force-reinstall "rich>=13.0"`).


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
         echo "Zsh Warning: llm-style script not found/runnable at '$_LLM_STYLE_SCRIPT_PATH'. Running 'llm' without styling." >&2
         command llm "$@" # Run original llm directly as fallback
         return $?
      fi

      # Run the original llm and pipe to the style script with the chosen style
      # Ensure python executable is correct (e.g., python3 or just python)
      command llm "$@" | python "$_LLM_STYLE_SCRIPT_PATH" --style "$_LLM_STYLE_DEFAULT_FILE"
      # Preserve the exit status of the pipe (Zsh specific: index 2 is the python script)
      # For Bash, use: return ${PIPESTATUS[1]}
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


Limitations
-----------

*   **Inline Parsing:** Basic regex parsing may fail on complex nested Markdown (e.g., bold inside italic within a link).
*   **Inline Styles in Code Blocks:** Inline Markdown formatting (like bold, italic, or transformations) is **not** applied within fenced code blocks (``` ```) as their content is treated literally.
*   **Regex Dependency:** Output quality depends heavily on `detection.json` patterns.
*   **Block State Machine:** Simple logic may break on complex, interleaved, or malformed block structures (code, quotes, lists).
*   **Color Transformation Robustness:** See note above regarding environment issues and base color conversion limitations.
*   **Performance:** Very large inputs might experience slower processing.


Future Development
------------------

*   **Testing:** Implement a robust test suite, focusing on edge cases, transformations, and parsing robustness.
*   **`llm` Plugin:** Develop an official plugin for Simon Willison's ``llm`` tool.
*   **Enhanced Inline Parsing:** Investigate more robust methods for handling inline markup.
*   **Configuration Options:** Configurable list indent width, guide chars, more Panel options.
*   **More Structure Detection:** Add rules for tables, definition lists if feasible.
*   **Performance Profiling:** Analyze and optimize for large inputs.
*   **Documentation:** Improve config/transform docs and troubleshooting guides.


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