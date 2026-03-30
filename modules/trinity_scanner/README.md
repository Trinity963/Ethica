
# Trinity Folder Scanner

This tool performs a full recursive scan of a given directory and outputs a JSON report.

## Usage

```bash
python3 trinity_folder_scanner.py /path/to/target --depth 4
```

- `--depth`: Optional. Maximum depth to recurse into folders (default: 10).
- Output is saved inside the `scans/` folder as a timestamped JSON file.

## Example

```bash
python3 trinity_folder_scanner.py /- - -/ --depth 4
```
