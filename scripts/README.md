# IBEX Scripts

This directory contains utility scripts for IBEX development and operations.

## Scripts

### `populate_changes.py`
Utility script to manually populate the IBEX state with current git changes.

**Usage:**
```bash
cd /path/to/project
python scripts/populate_changes.py
```

**Purpose:**
- Scans for modified files in git
- Adds them to `.ibex/state.json`
- Useful for recovering state or manual testing

### `start_self_monitoring.py`
Script to start IBEX self-monitoring mode.

**Usage:**
```bash
python scripts/start_self_monitoring.py
```

**Purpose:**
- Monitors the IBEX codebase itself
- Provides analysis of IBEX development
- Useful for IBEX contributors

## Development Scripts

These scripts are primarily for development and debugging purposes. They are not required for normal IBEX usage.

## Note

For regular IBEX usage, use the main `ibex` command:

```bash
ibex init "Your project intent"
ibex watch
ibex stake "checkpoint name"
```

See the main [README](../README.md) for full documentation.
