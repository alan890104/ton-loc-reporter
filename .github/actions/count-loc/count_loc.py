import os
import json
import argparse
import requests

# Predefined language-specific configurations
LANGUAGE_CONFIGS = {
    ".fc": {
        "extensions": [".fc", ".func"],
        "single_line_comment": ";;",
        "block_comment_start": "{-",
        "block_comment_end": "-}",
        "import_statement": "#include"
    },
    ".tolk": {
        "extensions": [".tolk"],
        "single_line_comment": "//",
        "block_comment_start": "/*",
        "block_comment_end": "*/",
        "import_statement": "import"
    }
}

def get_language_config(language):
    """Retrieve the configuration for a specific language."""
    config = LANGUAGE_CONFIGS.get(language)
    if not config:
        raise ValueError(f"Unsupported language: {language}")
    return config

def count_code_lines(directory, config, ignore_folders, ignore_files):
    """Count lines of code based on the provided configuration."""
    extensions = config["extensions"]
    single_line_comment = config["single_line_comment"]
    block_comment_start = config["block_comment_start"]
    block_comment_end = config["block_comment_end"]
    import_statement = config["import_statement"]

    total_lines = 0
    total_code_lines = 0
    in_multiline_comment = False

    for root, dirs, files in os.walk(directory):
        # Resolve full paths for ignored folders
        relative_ignore_folders = [os.path.join(directory, folder) for folder in ignore_folders]
        dirs[:] = [d for d in dirs if os.path.join(root, d) not in relative_ignore_folders]
        
        for file in files:
            full_path = os.path.join(root, file)
            # Resolve full paths for ignored files
            relative_ignore_files = [os.path.join(directory, file) for file in ignore_files]
            if full_path in relative_ignore_files:
                continue
            if any(file.endswith(ext) for ext in extensions):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            total_lines += 1
                            stripped_line = line.strip()

                            # Skip empty lines
                            if not stripped_line:
                                continue

                            # Handle multiline comments
                            if in_multiline_comment:
                                if block_comment_end in stripped_line:
                                    in_multiline_comment = False
                                    # Check for code after block_comment_end
                                    comment_end_idx = stripped_line.find(block_comment_end) + len(block_comment_end)
                                    if stripped_line[comment_end_idx:].strip():
                                        total_code_lines += 1
                                continue
                            if block_comment_start in stripped_line:
                                in_multiline_comment = True
                                # Check for code before block_comment_start
                                comment_start_idx = stripped_line.find(block_comment_start)
                                if stripped_line[:comment_start_idx].strip():
                                    total_code_lines += 1
                                continue

                            # Skip single-line comments and import statements
                            if (stripped_line.startswith(single_line_comment) or
                                stripped_line.startswith(import_statement)):
                                continue

                            # Count code lines
                            total_code_lines += 1
                except (OSError, IOError) as e:
                    print(f"Error reading file {full_path}: {e}")

    return total_code_lines

def post_comment_to_pr(message):
    """Post a comment to a GitHub pull request using environment variables."""
    repo = os.getenv("GITHUB_REPOSITORY")
    token = os.getenv("GITHUB_TOKEN")
    event_path = os.getenv("GITHUB_EVENT_PATH")

    if not repo or not token or not event_path:
        print("Missing required environment variables for GitHub integration.")
        return

    # Load the GitHub event JSON
    with open(event_path, "r") as f:
        event = json.load(f)

    pr_number = event.get("pull_request", {}).get("number")
    if not pr_number:
        print("This action must be triggered by a pull request event.")
        return

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"body": message}

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        print("Successfully posted the comment to the pull request.")
    else:
        print(f"Failed to post comment: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Count lines of code in a directory.")
    parser.add_argument("--directory", required=True, help="Directory to scan for code files.")
    parser.add_argument("--language", required=True, choices=LANGUAGE_CONFIGS.keys(), help="Programming language (e.g., .fc, .tolk).")
    parser.add_argument("--ignore-folders", action="append", default=[], help="Folders to ignore (relative to the directory). Use multiple times for multiple folders.")
    parser.add_argument("--ignore-files", action="append", default=[], help="Files to ignore (relative to the directory). Use multiple times for multiple files.")

    args = parser.parse_args()

    try:
        # Normalize relative paths based on the provided directory
        directory = os.path.abspath(args.directory)
        ignore_folders = [os.path.normpath(folder) for folder in args.ignore_folders]
        ignore_files = [os.path.normpath(file) for file in args.ignore_files]

        config = get_language_config(args.language)
        code_lines = count_code_lines(directory, config, ignore_folders, ignore_files)
        print(f"Total code lines in {args.language} files: {code_lines}")

        # Post comment to GitHub PR
        message = f"**Lines of Code Statistics**\n\nTotal lines of code: **{code_lines}**"
        post_comment_to_pr(message)
    except ValueError as e:
        print(e)
