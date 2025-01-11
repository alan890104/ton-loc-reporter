# TON LOC Reporter

This GitHub Action calculates Lines of Code (LOC) for TON smart contract projects and posts the results to pull requests.

## Inputs

### `directory`

**Required** The directory to scan for code files. Default is `.`.

### `language`

**Required** The programming language to analyze (e.g., `.fc`, `.tolk`).

### `ignore-folders`

Optional. Comma-separated list of folders to ignore. (Relative path to the project root)

### `ignore-files`

Optional. Comma-separated list of files to ignore. (Relative path to the project root)

## Example Usage

```yaml
name: Count Lines of Code

on:
  pull_request:

jobs:
  loc-report:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Run LOC Reporter
        uses: alan890104/ton-loc-reporter-action@v1.0
        with:
          directory: "./contracts"
          language: ".fc"
          ignore-folders: "mock,imports"
          ignore-files: "example.fc,pool/utils.fc"
```
