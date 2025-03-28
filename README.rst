================================================
llm-style: Rich Terminal Styling for LLM Output
================================================

Rich terminal styling for Markdown-like LLM output using panels, trees, inline styles, and configurable regex rules.

.. figure:: /path/to/screenshot.png
   :alt: Screenshot showing styled LLM output

   *(Add a screenshot here showing an example of styled output)*


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
    *   `styles.json`: Define named styles using ``rich``'s powerful syntax.
*   **Rich Output:** Leverages the ``rich`` library for:
    *   Colors (Truecolor, 256, basic).
    *   Styles (bold, italic, underline, dim, etc.).
    *   Panel borders around code blocks and blockquotes.
    *   Tree guide lines for nested lists.
    *   Basic inline styling (bold, italic, code).
    *   Syntax highlighting for code blocks (requires ``pygments``).
*   **Flexible Detection:** Uses regex for primary structure detection, allowing custom rules beyond standard Markdown.
*   **Pipeline Friendly:** Designed to be used in standard Unix pipelines (e.g., ``llm ... | llm-style.py``).
*   **Debug Mode:** Includes a ``--debug`` flag for verbose configuration loading/validation output.
*   **Markup Preservation:** Optional ``--keep-markup`` flag to display original block markup characters (``#``, ``*``, ``**``).


Installation
------------

1.  **Prerequisites:**
    *   Python 3.7+
    *   `pip` (Python package installer)

2.  **Required Libraries:**
    *   `rich`: The core rendering library.
    *   `pygments` (Optional, but Recommended): For syntax highlighting within code blocks.

    Install them using pip:

    .. code-block:: bash

        pip install rich pygments

3.  **Get the Script:**
    *   Clone this repository:

        .. code-block:: bash

            git clone https://github.com/gagin/llm-style.git
            cd llm-style

    *   Or, download the `llm-style.py` script directly.

4.  **Make Executable (Optional):**

    .. code-block:: bash

        chmod +x llm-style.py


Usage
-----

``llm-style`` reads text from standard input and prints styled output to standard output.

**Basic Usage:**

Pipe the output of any command (like ``llm``) into the script:

.. code-block:: bash

    llm "Explain the difference between lists and tuples in Python using markdown" | python llm-style.py
    # Or if executable:
    # llm ... | ./llm-style.py

**Keeping Block Markup:**

To see the original ``#``, ``*``, etc., characters (while still applying colors/styles):

.. code-block:: bash

    llm ... | python llm-style.py --keep-markup

**Debugging Configuration:**

To see verbose output about configuration loading and validation:

.. code-block:: bash

    llm ... | python llm-style.py --debug

**Using Custom Configuration Directory:**

.. code-block:: bash

    llm ... | python llm-style.py --config-dir /path/to/my/configs/

*(Note: Replace ``python llm-style.py`` with ``./llm-style.py`` if you made it executable and are in the correct directory).*


Comparison with Other Tools
---------------------------

Tools like `glow`_, `mdcat`_, and `bat`_ are excellent terminal Markdown renderers/viewers. Why use ``llm-style``?

*   **Strictness:** Tools like ``glow`` or ``mdcat`` often expect reasonably valid CommonMark or GitHub Flavored Markdown. They might produce errors or poor formatting if the LLM output deviates significantly (e.g., inconsistent indentation, malformed lists, unusual syntax). ``llm-style`` uses regex and is designed to be more forgiving of "Markdown-like" text.
*   **Flexibility vs. Robustness:** Standard Markdown renderers have robust parsers for *Markdown*, handling complex nesting and edge cases correctly, including inline formatting. ``llm-style``'s regex-based approach (especially for inline elements) is less robust for pure Markdown but offers the flexibility to style arbitrary, non-Markdown patterns defined in ``detection.json``.
*   **Unique Rendering:** ``llm-style`` leverages ``rich`` features not typically found in standard Markdown viewers:
    *   **Panels:** Draws borders around code blocks and blockquotes.
    *   **Trees:** Draws guide lines for nested lists.
*   **Configuration:** ``llm-style`` offers direct JSON configuration for detection patterns, style mapping, and `rich` styles. Other tools rely on their specific theme formats (e.g., Sublime Text themes for ``bat``, YAML/JSON for ``glow``).

**Choose ``llm-style`` if:**

*   Your input is often "Markdown-like" but not strictly valid.
*   You want the specific visual structure provided by Panels and Trees.
*   You need to style custom text patterns beyond standard Markdown using regex.
*   You prefer direct JSON configuration tied to ``rich``.

**Choose standard tools (``glow``, ``bat``, ``mdcat``) if:**

*   Your input is reliably well-formed Markdown.
*   Robust handling of all Markdown features (especially complex inline/nested elements) is the top priority.
*   You prefer using existing theme ecosystems (e.g., for ``bat``).

.. _glow: https://github.com/charmbracelet/glow
.. _mdcat: https://github.com/swsnr/mdcat
.. _bat: https://github.com/sharkdp/bat


Configuration
-------------

On the first run, if the configuration directory doesn't exist, ``llm-style`` will create default configuration files. By default, this is in ``~/.config/llm-style/``.

*   **`detection.json`:** Maps rule names to Python regex patterns. Includes special rules for blocks and inline formatting.
*   **`mapping.json`:** Maps rule names to style names or block configurations (borders, guides, etc.). Requires ``"default_text"``.
*   **`styles.json`:** Maps style names to style definitions compatible with ``rich``.

See the default files for examples.


Color Guide (Using `rich` Styles)
---------------------------------

The styles defined in ``styles.json`` use the syntax understood by the `rich`_ library. Understanding how `rich` handles colors is key to effective customization.

**Why "tan" works but "brown" might not (by default):**

*   **Standard Names:** `rich` supports standard `W3C/CSS color names`_. "tan" is one of these standard names. While "orange" is also standard, "brown" itself is less common in the basic set than variations like "sienna", "saddlebrown", "maroon", etc. If a simple name doesn't work, it might not be in the standard list `rich` uses.

**How to Specify Colors:**

If a simple name isn't recognized or you want a specific shade, `rich` offers several powerful alternatives:

1.  **Standard Color Names:** Use common names like ``"red"``, ``"green"``, ``"blue"``, ``"yellow"``, ``"magenta"``, ``"cyan"``, ``"white"``, ``"black"``, and other W3C names like ``"tan"``, ``"wheat"``, ``"lightblue"``, ``"purple"``.

    *Example:* ``"style_header1": "bold bright_blue underline"``

2.  **Hex Codes (Truecolor):** For terminals supporting Truecolor (most modern ones), use CSS-style hex codes.

    *Example (Orange):* ``"style_warning": "#FFA500"`` (or shorthand ``"#FA0"``)
    *Example (A Brown):* ``"style_custom_brown": "#A52A2A"``

3.  **RGB Tuples (Truecolor):** Specify RGB values from 0-255.

    *Example (Orange):* ``"style_warning": "rgb(255,165,0)"``
    *Example (A Brown):* ``"style_custom_brown": "rgb(165,42,42)"``

4.  **Numbered Colors (256-Color Terminals):** Use numbers 0-255 for compatibility with terminals supporting 256 colors. Finding the exact number might require looking at a 256-color chart (search online for "xterm 256 color chart").

    *Example (Gold/Orange):* ``"style_warning": "color(178)"``
    *Example (A Brown):* ``"style_custom_brown": "color(131)"`` (approximate)

**Combining with Attributes:**

You can combine colors with attributes like ``bold``, ``italic``, ``underline``, ``dim``, ``strike``, and background colors using ``on <color>``.

*Example:* ``"style_error": "bold white on red"``
*Example:* ``"style_comment": "italic color(245)"`` (italic light grey)

**Recommendation:**

*   Start with standard names for common colors.
*   Use hex codes or RGB for specific shades if your terminal supports Truecolor.
*   Use numbered colors if you need broader compatibility with 256-color terminals.
*   Refer to the `rich Style documentation`_ for the most comprehensive details.

.. _rich: https://github.com/Textualize/rich
.. _W3C/CSS color names: https://www.w3.org/wiki/CSS/Properties/color/keywords


Limitations
-----------

*   **Inline Parsing:** The current inline parsing (for bold, italic, code) uses regex and is basic. It may not correctly handle complex nesting or edge cases found in full Markdown implementations.
*   **Regex Dependency:** The quality of the output heavily depends on the accuracy and comprehensiveness of the regex patterns in `detection.json`. Poorly written regexes can lead to misidentified structures.
*   **Block State Machine:** The logic for handling code blocks and blockquotes is relatively simple and might break on complex, interleaved structures.
*   **Performance:** While generally performant for typical LLM output sizes, extremely large inputs might experience slower processing due to the regex and line-by-line state management.


Future Development
------------------

*   **Style Library / Themes:** Create pre-defined sets of configuration files (themes) and allow easy switching via a command-line argument (e.g., ``--theme solarized``).
*   **Testing:** Implement a robust test suite, particularly focusing on edge cases and "weird" text inputs to improve parsing robustness.
*   **`llm` Plugin:** Develop an official plugin for Simon Willison's ``llm`` tool for seamless integration (e.g., ``llm ... --format=llm-style``).
*   **Shell Integration:** Provide examples or helper functions/aliases for shells (like ``.zshrc`` or ``.bashrc``) to automatically pipe ``llm`` output through ``llm-style.py`` (e.g., wrapping the ``llm`` command).
*   **Enhanced Inline Parsing:** Investigate more robust methods for handling inline markup, potentially using a more advanced regex approach or a limited custom parser (balancing flexibility with complexity).
*   **Configuration Options:**
    *   Make list indentation width configurable.
    *   Allow customization of Tree guide characters.
    *   Expose Panel padding/options via `mapping.json`.
*   **More Structure Detection:** Add rules and logic to detect and style other common elements like tables or definition lists.
*   **Performance Profiling:** Analyze performance on large inputs and optimize if necessary.
*   **Documentation:** Improve documentation for creating custom configurations and understanding the detection logic.


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