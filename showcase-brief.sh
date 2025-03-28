#!/bin/bash
# Or use #!/bin/zsh

# --- Configuration ---
# Assume llm-style.py is in the current directory
LLM_STYLE_SCRIPT="./llm-style.py" # Use relative path

# Sample text focuses on key elements for comparison
SAMPLE_MARKDOWN='Normal text, *italic*, **bold**.\n* List Item (Level 0)'
# Use H1 for the style name header within the sample
HEADER_MARKDOWN_PREFIX='# Style: '

# --- Script Start ---

# Check if the main script exists and is runnable
if [[ ! -f "$LLM_STYLE_SCRIPT" || (! -r "$LLM_STYLE_SCRIPT" && ! -x "$LLM_STYLE_SCRIPT") ]]; then
    # Try with python explicitly if not directly executable
    if ! python "$LLM_STYLE_SCRIPT" --help > /dev/null 2>&1; then
        echo "Error: llm-style.py script not found or not runnable with python at '$LLM_STYLE_SCRIPT'" >&2
        exit 1
    fi
     echo "Info: llm-style.py is not directly executable, will run using 'python $LLM_STYLE_SCRIPT'" >&2
fi

# --- Run with Default Style First ---
echo "--- Running with Default Style (styles.json or internal) ---"
# Construct the markdown sample including a header indicating "Default"
default_header="${HEADER_MARKDOWN_PREFIX}DEFAULT (styles.json)"
full_sample_default=$(printf '%s\n\n%s' "$default_header" "$SAMPLE_MARKDOWN")

# Pipe the sample to llm-style.py *without* the --style flag
# Relying on script to create/use default configs in ~/.config/llm-style
# OR use --config-dir . if detection/mapping should also be local/defaulted
# Using ~/.config/llm-style for default run seems more standard
printf '%b\n' "$full_sample_default" | python "$LLM_STYLE_SCRIPT" # No --style or --config-dir here

# Add separation
echo
echo "---------------------------------------"
echo

# --- Find and Loop Through Specific Style Files ---
shopt -s nullglob
style_files=(*style.json *styles.json)
shopt -u nullglob

if [ ${#style_files[@]} -eq 0 ]; then
  echo "No *style.json or *styles.json files found in the current directory to compare."
  # Don't exit if default run was successful
else
  echo "--- Comparing Specific Style Files in Current Directory ---"
  for style_file in "${style_files[@]}"; do
      # Construct the full markdown sample including the styled header
      full_sample_markdown=$(printf '%s\n\n%s' "${HEADER_MARKDOWN_PREFIX}${style_file}" "$SAMPLE_MARKDOWN")

      # Pipe the combined sample to llm-style.py for this specific style
      # Using --config-dir . assumes detection/mapping are also local or defaults okay
      printf '%b\n' "$full_sample_markdown" | python "$LLM_STYLE_SCRIPT" --config-dir . --style "$style_file"

      # Add just one blank line for separation
      echo

  done
  echo "---------------------------------------"
fi

echo "Style comparison complete."