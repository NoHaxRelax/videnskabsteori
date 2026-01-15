# SDGUI File Merger

This script merges multiple `.sdgui` files into a single combined file.

## What It Does

The script combines:
- **All effects** from all files (keeping unique ones)
- **All impacts** from all files (keeping unique ones)
- **All scenarios** with their impact assignments merged together
- **Globals** and metadata from the files

## Usage

### Basic Usage
```bash
python merge_sdgui.py
```
This will merge all `.sdgui` files in the current directory and create `combined.sdgui`.

### Specify Target Folder
```bash
python merge_sdgui.py "path/to/folder"
```

### Specify Output Filename
```bash
python merge_sdgui.py . "merged-group19.sdgui"
```

### Full Example
```bash
python merge_sdgui.py "C:\Users\Elias\Desktop\DTU BCs\KAIST\videnskabsteori" "final-merged.sdgui"
```

## What Gets Merged

### ✓ Effects
All unique effects (lifecycle activities) are combined. If the same effect ID appears in multiple files, only one copy is kept.

### ✓ Impacts  
All SDG impacts are combined. Each impact assessment from each file is included in the final merged file.

### ✓ Scenarios
Scenarios with the same ID are merged together. Impact assignments from all files are combined so you get all team members' assessments in one scenario.

### ✓ Metadata
- Takes the `gitHash` from any of the input files
- Combines `globals` (authors, project name, lifecycle stages)

## Output Example

```
============================================================
SDGUI File Merger
============================================================
Target folder: .
Output file: merged-group19.sdgui
============================================================
Found 2 .sdgui files to merge:
  - elias.sdgui
  - group-.sdgui

Processing elias.sdgui...
  Added effect: Smelting the metals
  ...
  Added impact: iid-1XE46953C1OSjG8eLLJwl -> SDG 13 on 'Production of fiberglass and reinforced plastic'
  ...
  Added scenario: Untitled scenario
  ...

[SUCCESS] Merge complete!
  Total effects: 30
  Total impacts: 8
  Total scenarios: 1
  Output file: merged-group19.sdgui
```

## Notes

- The script automatically excludes the output file from being merged (so you can run it multiple times)
- Duplicate IDs are handled automatically - only unique items are kept
- Works with any number of `.sdgui` files in the folder
- The output file maintains the same format and structure as the input files
