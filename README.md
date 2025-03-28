> Colors are perception, child. We decide what they mean.
>
> -- Inspired by themes in Brandon Sanderson's *Warbreaker*

# llm-style: Rich Terminal Styling for LLM Output

**Version: 0.6.0**

Rich terminal styling for Markdown-like LLM output using panels, trees, inline styles, dynamic color transformations, and configurable regex rules.

<figure>
<img src="example.png" alt="example.png" />
<figcaption><em>(Above: Example using the ``tan-crazybold-style.json`` theme. The "crazy" reverse video for bold is intentional for high contrast.)</em></figcaption>
</figure>

## Motivation

Raw text output from LLMs can be hard to read, especially when it contains structural elements like headers, lists, or code blocks but isn't always perfectly valid Markdown. Standard Markdown renderers might fail or produce suboptimal results on this "Markdown-like" text.

`llm-style` aims to bridge this gap by using a combination of configurable regular expressions and a state machine to detect common structural elements and apply rich formatting (colors, bold, italic, panels, tree guides) using the excellent `rich` Python library, making the output significantly more readable directly in the terminal.

## Key Features

- **Markdown-like Aware:** Designed to handle common structures found in LLM output, even if not strictly valid Markdown.
- **Highly Configurable:** Uses simple JSON files for:
  - \`detection.json\`: Define regex patterns to identify structures.
  - \`mapping.json\`: Map detected structures to style names or block configurations.
  - <span class="title-ref">\<style-file\>.json</span> (e.g., <span class="title-ref">styles.json</span>, <span class="title-ref">green-theme.json</span>): Define named styles using <span class="title-ref">rich</span>'s powerful syntax, including dynamic transformations.
- **Rich Output:** Leverages the `rich` library for:
  - Colors (Truecolor, 256, basic).
  - Styles (bold, italic, underline, dim, reverse, etc.).
  - **Panels:** Draws borders around code blocks and blockquotes.
  - **Trees:** Draws guide lines for nested lists.
  - Syntax highlighting for code blocks (requires `pygments`).
- **Dynamic Inline Styles:** Configure inline styles (like bold) to dynamically adjust color (brightness, saturation, hue) based on the surrounding text's color.
- **Style Themes:** Load different style definitions using the `--style` argument. The default is <span class="title-ref">styles.json</span>.
- **Flexible Detection:** Uses regex for primary structure detection, allowing custom rules beyond standard Markdown.
- **Pipeline Friendly:** Designed to be used in standard Unix pipelines (e.g., `llm ... | llm-style.py`).
- **Shell Integration:** Optional shell function (Zsh example provided) to automatically pipe <span class="title-ref">llm</span> output.
- **Debug Mode:** Includes a `--debug` flag for verbose configuration loading/validation and transformation output.
- **Markup Preservation:** Optional `--keep-markup` flag to display original block markup characters (<span class="title-ref">\#</span>, <span class="title-ref">\*</span>, <span class="title-ref">\*\*</span>).

## Installation

1.  **Prerequisites:**

    - Python 3.7+ (May need 3.8+ for full <span class="title-ref">colorsys</span> support if not built-in)
    - <span class="title-ref">pip</span> (Python package installer)

2.  **Required Libraries:**

    - \`rich\`: The core rendering library. (Version 13+ recommended).
    - <span class="title-ref">pygments</span> (Optional, but Recommended): For syntax highlighting within code blocks.
    - <span class="title-ref">colorsys</span> (Usually built-in with Python): Required for dynamic color transformations. If missing, transforms will be skipped.

    Install them using pip:

    ``` bash
    pip install "rich>=13.0" pygments
    ```

3.  **Get the Script:**

    - Clone this repository or download the <span class="title-ref">llm-style.py</span> script directly.

      ``` bash
      # Example if cloning
      git clone https://github.com/gagin/llm-style.git
      cd llm-style
      ```

4.  **Make Executable (Optional):**

    ``` bash
    chmod +x llm-style.py
    ```

## Usage

`llm-style` reads text from standard input and prints styled output to standard output. It's designed to be used in a pipeline.

**Basic Usage (Default Style):**

Pipe the output of the `llm` command (or any text-producing command) into the script. This uses <span class="title-ref">styles.json</span> in your config directory (by default <span class="title-ref">~/.config/llm-style/</span>), creating it with a default green theme if it doesn't exist.

``` bash
llm "Explain Python decorators" | python llm-style.py
# Or if executable:
# llm "Explain Python decorators" | ./llm-style.py
```

**Using a Specific Style Theme:**

Use the `--style` argument to specify a different JSON file located within your config directory.

``` bash
# Assuming you have ~/.config/llm-style/tan-crazybold-style.json
llm "Pros and cons" | python llm-style.py --style tan-crazybold-style.json
```

**Using a Local Style File (without copying):**

You can use a style file from the current directory by setting the config directory to <span class="title-ref">.</span> *if* you also have <span class="title-ref">detection.json</span> and <span class="title-ref">mapping.json</span> present in the current directory (or you allow the script to create defaults there).

``` bash
# Assumes my-local-style.json, detection.json, mapping.json are in '.'
llm "Use local style" | python llm-style.py --config-dir . --style my-local-style.json
```

**Using Shell Integration (Recommended for Convenience):**

If you've added the provided Zsh function (see "Shell Integration" section) to your `.zshrc`, you can just use the `llm` command directly, and it will automatically be styled using your configured preference:

``` bash
# Assumes the 'llm' function is defined in .zshrc to pipe through the styler
llm "This output will be automatically styled"
```

**Keeping Block Markup:**

``` bash
llm "Show raw markdown" | python llm-style.py --keep-markup
```

**Debugging Configuration:**

Redirect standard output to <span class="title-ref">/dev/null</span> and error/debug output to a file to isolate debug messages.

``` bash
llm "Debug this" | python llm-style.py --debug --style my-debug-style.json > /dev/null 2> debug.log
```

*(Note: Replace \`\`python llm-style.py\`\` with \`\`./llm-style.py\`\` if executable and in the correct path/directory).*

## `--help` Output

``` text
usage: llm-style.py [-h] [--config-dir CONFIG_DIR] [--style STYLE] [--debug] [--keep-markup]

Apply styles to text input based on configurable rules.

options:
  -h, --help            show this help message and exit
  --config-dir CONFIG_DIR
                        Directory containing detection.json, mapping.json, and style JSON files. (default: ~/.config/llm-style)
  --style STYLE         Filename of the style definitions JSON file (e.g., 'styles.json', 'calm-styles.json') within the config directory. (default: styles.json)
  --debug               Enable debug/verbose output to stderr. (default: False)
  --keep-markup         Keep original Markdown block characters (e.g., '#', '*', '>') in the output. (default: False)
```

## Comparison with Other Tools

*(This section remains largely the same - highlighting flexibility for "Markdown-like" text, unique rendering via Rich (Panels/Trees), and configuration)*

Tools like [glow](https://github.com/charmbracelet/glow), [mdcat](https://github.com/swsnr/mdcat), and [bat](https://github.com/sharkdp/bat) are excellent terminal Markdown renderers/viewers. Why use `llm-style`?

- **Strictness:** Tools like <span class="title-ref">glow</span> or <span class="title-ref">mdcat</span> often expect reasonably valid CommonMark or GitHub Flavored Markdown... <span class="title-ref">llm-style</span> uses regex and is designed to be more forgiving...
- **Flexibility vs. Robustness:** Standard Markdown renderers have robust parsers... <span class="title-ref">llm-style</span>'s regex-based approach... offers the flexibility to style arbitrary, non-Markdown patterns...
- **Unique Rendering:** <span class="title-ref">llm-style</span> leverages `rich` features... Panels... Trees...
- **Configuration:** <span class="title-ref">llm-style</span> offers direct JSON configuration... including dynamic transformations.

**Choose \`\`llm-style\`\` if:**

- Your input is often "Markdown-like" but not strictly valid.
- You want the specific visual structure provided by Panels and Trees.
- You need to style custom text patterns beyond standard Markdown using regex.
- You want dynamic inline styling based on context.
- You prefer direct JSON configuration tied to `rich` and want theme support.

**Choose standard tools (\`\`glow\`\`, \`\`bat\`\`, \`\`mdcat\`\`) if:**

- Your input is reliably well-formed Markdown.
- Robust handling of all Markdown features... is the top priority.
- You prefer using existing theme ecosystems...

## Configuration

On the first run, if the configuration directory (default: `~/.config/llm-style/`) or the default config files don't exist, `llm-style` will create them with default settings (based on a greenish theme).

- **\`detection.json\`:** Maps rule names to Python regex patterns for structure detection.
- **\`mapping.json\`:** Connects rule names from <span class="title-ref">detection.json</span> to style names or special block configurations (like panels). Requires `"default_text"`.
- **\`\<style-file\>.json\`** (e.g., <span class="title-ref">styles.json</span>, specified via `--style`): Maps style names (referenced in <span class="title-ref">mapping.json</span>) to `rich` style definitions. This is where colors, attributes, and dynamic transformations are defined.

**Recommendation:** Copy the default <span class="title-ref">styles.json</span> generated by the script or provided theme examples (like <span class="title-ref">tan-crazybold-style.json</span>) from the source repository into your <span class="title-ref">~/.config/llm-style/</span> directory. Use these as starting points for your own customization by editing the JSON files.

## Color Guide (Using <span class="title-ref">rich</span> Styles)

The styles defined in your style JSON file use the syntax understood by the [rich](https://github.com/Textualize/rich) library.

**How to Specify Colors:**

1.  **Standard Color Names:** Use common names like `"red"`, `"green"`, `"blue"`, `"yellow"`, `"magenta"`, `"cyan"`, `"white"`, `"black"`. Hex codes are generally more reliable than less common names.
2.  **Hex Codes (Truecolor):** Recommended for specific colors if your terminal supports Truecolor. Example: `"#FFA500"` (Orange), `"#A0522D"` (Sienna).
3.  **RGB Tuples (Truecolor):** Specify RGB values from 0-255. Example: `"rgb(255,165,0)"`.
4.  **Numbered Colors (256-Color Terminals):** Use numbers 0-255. Example: `"color(178)"` (Gold/Orange).

**Combining with Attributes:**

Combine colors with attributes like `bold`, `italic`, `underline`, `dim`, `strike`, `reverse`, and background colors using `on <color>`.

*Example:* `"style_error": "bold white on red"` *Example:* `"style_inline_bold": "bold reverse"`

Refer to the [rich Style documentation](https://rich.readthedocs.io/en/latest/style.html) for comprehensive details.

Inline Style Customization & Transformations ------------------------------------------

Inline styles (<span class="title-ref">bold</span>, <span class="title-ref">italic</span>, <span class="title-ref">code</span>) are handled via rules like <span class="title-ref">inline_bold_star</span>, <span class="title-ref">inline_code</span>, etc., in <span class="title-ref">detection.json</span>. These implicitly map to styles named <span class="title-ref">style_inline_bold</span>, <span class="title-ref">style_inline_italic</span>, and <span class="title-ref">style_inline_code</span> in your active style JSON file.

You can define these styles in two ways:

1.  **Simple String:** Uses standard <span class="title-ref">rich</span> style syntax. The style is applied directly. If only an attribute (like <span class="title-ref">italic</span>) is given, the color is inherited from the surrounding text.

    ``` json
    {
      "style_inline_italic": "italic",
      "style_inline_code": "yellow on grey19",
      "style_inline_bold": "bold reverse"
    }
    ```

2.  **Object with Transformation:** Allows dynamic color adjustment based on the surrounding text's color. Requires the <span class="title-ref">colorsys</span> Python module.

    ``` json
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
    ```

    - \`"attributes"\`: (String) Basic <span class="title-ref">rich</span> style attributes (e.g., <span class="title-ref">"bold"</span>, <span class="title-ref">"bold underline"</span>).
    - \`"transform"\`: (Object, Optional) Rules for color modification (<span class="title-ref">adjust_brightness</span>, <span class="title-ref">adjust_saturation</span>, <span class="title-ref">shift_hue</span>). See details in the source code or previous README versions if needed.

    **How it works:** The script gets the base color. If a <span class="title-ref">transform</span> object is defined, it attempts HSL adjustments and uses the *new* color with the defined <span class="title-ref">attributes</span>. If transformation fails (e.g., base color unusable), only <span class="title-ref">attributes</span> are applied.

**Important Note:** Inline styling (including transformations) is **not** applied within fenced code blocks (`` ` ``\`). The content of code blocks is treated literally to preserve code structure and syntax.

A Note on Color Transformations and <span class="title-ref">rich</span> / Environment Issues -------------------------------------------------------------

*(This section remains largely the same - explains the dependency on \`colorsys\` and RGB conversion, the observed AttributeErrors, the integer-value workaround in the script, and recommends checking environment/reinstalling rich if issues persist)*

... The <span class="title-ref">\_apply_transform</span> function in <span class="title-ref">llm-style.py</span> includes a workaround that avoids directly referencing <span class="title-ref">ColorType.RGB</span> or <span class="title-ref">ColorType.SYSTEM</span> attributes by name. Instead, it checks the integer value of the color type (<span class="title-ref">int(base_color.type)</span>)...

**Caveats:** \* This workaround relies on internal integer values... \* Transformations may still fail if <span class="title-ref">get_truecolor()</span> cannot resolve certain base colors... \* If you encounter persistent issues... ensure a clean Python environment... (<span class="title-ref">pip install --force-reinstall "rich\>=13.0"</span>).

## Shell Integration (Optional)

For convenience, you can add a function to your shell's configuration file (e.g., <span class="title-ref">.zshrc</span> for Zsh, <span class="title-ref">.bashrc</span> for Bash) to automatically pipe the output of the <span class="title-ref">llm</span> command through the styler.

**Example for \`.zshrc\`:**

This function overrides the default <span class="title-ref">llm</span> command.

``` zsh
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
```

**Setup:** 1. **Edit** the function above, setting <span class="title-ref">\_LLM_STYLE_SCRIPT_PATH</span> to the correct absolute path of your <span class="title-ref">llm-style.py</span> script. 2. **Set** <span class="title-ref">\_LLM_STYLE_DEFAULT_FILE</span> to the filename (within your <span class="title-ref">~/.config/llm-style/</span> directory) of the style theme you want to use by default (e.g., <span class="title-ref">"styles.json"</span>, <span class="title-ref">"tan-crazybold-style.json"</span>). 3. **Add** the edited function block to your <span class="title-ref">~/.zshrc</span> file. 4. **Reload** your shell configuration (<span class="title-ref">source ~/.zshrc</span> or open a new terminal).

Now, running <span class="title-ref">llm "your prompt"</span> will automatically apply the styling using your chosen default style file.

**Bypassing the Wrapper:** To run the original <span class="title-ref">llm</span> command without styling, use:  
`command llm "your prompt"` or `\llm "your prompt"`

## Limitations

- **Inline Parsing:** Basic regex parsing may fail on complex nested Markdown (e.g., bold inside italic within a link).
- **Inline Styles in Code Blocks:** Inline Markdown formatting (like bold, italic, or transformations) is **not** applied within fenced code blocks (`` ` ``\`) as their content is treated literally.
- **Regex Dependency:** Output quality depends heavily on <span class="title-ref">detection.json</span> patterns.
- **Block State Machine:** Simple logic may break on complex, interleaved, or malformed block structures (code, quotes, lists).
- **Color Transformation Robustness:** See note above regarding environment issues and base color conversion limitations.
- **Performance:** Very large inputs might experience slower processing.

## Future Development

- **Testing:** Implement a robust test suite, focusing on edge cases, transformations, and parsing robustness.
- **\`llm\` Plugin:** Develop an official plugin for Simon Willison's `llm` tool.
- **Enhanced Inline Parsing:** Investigate more robust methods for handling inline markup.
- **Configuration Options:** Configurable list indent width, guide chars, more Panel options.
- **More Structure Detection:** Add rules for tables, definition lists if feasible.
- **Performance Profiling:** Analyze and optimize for large inputs.
- **Documentation:** Improve config/transform docs and troubleshooting guides.

## Credits

This script was implemented by Google Gemini 2.5 Pro (Experimental Model 03-25), ideated, curated and iterated by the author, Alex Gaggin.

## License

MIT License

Copyright (c) 2025 Alex Gaggin

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
