# Teams Activity Keeper v2.4.0

A professional-grade terminal utility for preventing Microsoft Teams "Away" status.

## Key Features

- **Built-in Presets**: Quickly switch between usage scenarios (Stealth, Aggressive, Testing, Standard).
- **System Tray Integration**: Run in background with visual status indicator and menu controls.
- **Configuration Hot-reload**: Press 'C' to reload config file without restarting the script.
- **Hierarchical Configuration**: Merges profiles, presets, and CLI overrides seamlessly.
- **Smart Activity Patterns**: Randomizes mouse movements and keyboard keys for human-like behavior.
- **Inactivity Detection**: Automatically pauses when you are actually using your computer.
- **Schedule Management**: Define work hours and days to automate operation.
- **Verbose Diagnostic Mode**: Detailed logging for advanced users.

## Configuration Presets

Use the `--preset` flag to load one of our optimized configurations:

| Preset | Description | Key Settings |
| :--- | :--- | :--- |
| `stealth` | Maximum concealment | 3m intervals, Inactivity detection, Multi-method randomization. |
| `aggressive` | Guaranteed active state | 1m intervals, pure mouse jiggle. |
| `testing` | Fast validation | 10s intervals, sound notifications enabled. |
| `standard` | Balanced usage | Default 2m intervals. |

### Usage Examples

**List available presets:**
```bash
python activity_keeper.py --list-presets
```

**Run in stealth mode:**
```bash
python activity_keeper.py --preset stealth
```

**Save current CLI settings as a new preset:**
```bash
python activity_keeper.py --interval 300 --method keyboard --save-preset marathon
```

## Configuration Priority
The script merges configuration in this order (highest priority first):
1. **CLI Arguments** (`--interval`, `--method`, etc.)
2. **Preset** (`--preset`)
3. **Profile** (`--profile`)
4. **Default Config File** (`activity_config.json`)
5. **Internal Defaults**

## System Tray Integration

Run the script with a visual status indicator in your system tray (notification area).

### Features
- **Status Colors**: 
  - 🟢 Green = Running
  - 🟡 Yellow = Paused
  - 🔵 Blue = Waiting for schedule
- **Right-click Menu**: 
  - Pause
  - Resume
  - Exit
- **Background Operation**: Script runs silently in the background

### Usage

**Enable system tray:**
```bash
python activity_keeper.py --tray
```

**Combine with quiet mode for fully silent operation:**
```bash
python activity_keeper.py --tray --quiet --auto-restart
```

**Requirements:**
```bash
pip install pystray pillow
```

### Notes
- Icon appears in Windows notification area (bottom-right)
- Works with all other features (presets, hot-reload, etc.)
- Clean shutdown when selecting "Exit" from menu
- Auto-minimizes console when used with `--quiet`

## Configuration Hot-reload

Reload your configuration file without restarting the script.

### How It Works
1. Edit `activity_config.json` while script is running
2. Press **'C'** key in the console
3. Configuration reloads and applies immediately

### Reloadable Settings
Settings that apply immediately:
- `activity_interval`
- `pattern_randomization_enabled`
- `randomization_mouse_probability`
- `inactivity_detection_enabled`
- `inactivity_threshold_seconds`
- `sound_enabled` and sound settings
- `schedule_enabled` and schedule settings
- `schedule_warning_minutes`

Settings that require restart:
- `total_duration` (only affects new sessions with --auto-restart)
- `method` (unless pattern randomization is enabled)
- `keyboard_key`
- `mouse_move_distance`

### Usage

**During script execution:**
1. Edit `activity_config.json`
2. Press **'C'** key
3. See confirmation: "Configuration reloaded successfully!"

**Example:**
```bash
# Start with testing preset
python activity_keeper.py --preset testing --verbose

# While running:
# - Edit activity_config.json (change activity_interval to 15)
# - Press 'C' in the console
# - New interval applies to next activity cycle
```

### Safety
- Invalid configurations won't apply (keeps running with old config)
- Validation happens before applying changes
- File errors won't crash the script
- Clear feedback on success/failure
