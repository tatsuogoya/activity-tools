# Activity Tools

A collection of Python automation tools for keeping your system active and automating mouse actions.

## Tools Included

### 1. Teams Activity Keeper (`activity_keeper.py`)

Keep your PC active and Microsoft Teams status green without manual intervention. Features a beautiful console dashboard and smart scheduling.

**Features:**
- 🖱️ Mouse jiggling with randomized movements
- ⌨️ Keyboard activity simulation
- 🕐 Customizable activity intervals with randomization
- 📅 Smart scheduling (work hours and days)
- 🎯 Stay Awake mode (prevents Windows sleep)
- 📊 Real-time dashboard with statistics
- 🔑 Ghost key (F15) for activity registration
- 🛡️ Failsafe support (move mouse to corner to stop)

### 2. Mouse Automation (`mouse_automation.py`)

Automate mouse clicks at specific screen coordinates with human-like randomization.

**Features:**
- Configurable click coordinates
- Randomized timing and positioning
- Support for left and right clicks
- Dry-run mode for testing
- Activity logging

## Requirements

- Python 3.7+
- Windows 10/11 (for Stay Awake mode and console features)
- Dependencies: `pyautogui`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/tatsuogoya/activity-tools.git
cd activity-tools
```

2. Create a virtual environment (recommended):
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install pyautogui
```

## Usage

### Teams Activity Keeper

**Quick Start:**
```bash
python activity_keeper.py
```

**Using the batch file (recommended):**
```bash
Start_Teams_Keeper.bat
```

**Command-line options:**
```bash
python activity_keeper.py --interval 120 --duration 18000 --method mouse
```

**Options:**
- `--config` - Configuration file path (default: `activity_config.json`)
- `--interval` - Activity interval in seconds (default: 120)
- `--duration` - Total duration in seconds (default: 18000 = 5 hours)
- `--method` - Activity method: `mouse` or `keyboard` (default: `mouse`)

**Interactive controls:**
- Press **ESC** or **Q** to stop the program
- Dashboard updates in real-time
- Countdown shows time until next activity

### Mouse Automation

```bash
python mouse_automation.py --config config.json
```

**Options:**
- `--config` - Configuration file path
- `--log` - Log file path
- `--dry-run` - Simulate actions without moving mouse

## Configuration

### Activity Keeper (`activity_config.json`)

```json
{
    "activity_interval": 120,
    "total_duration": 18000,
    "method": "mouse",
    "keyboard_key": "scrolllock",
    "mouse_move_distance": 10,
    "schedule_enabled": false,
    "work_hours_start": "09:00",
    "work_hours_end": "17:00",
    "work_days": [1, 2, 3, 4, 5]
}
```

**Configuration options:**
- `activity_interval` - Seconds between activities (randomized ±10%)
- `total_duration` - How long to run (in seconds)
- `method` - `"mouse"` or `"keyboard"`
- `keyboard_key` - Key to press for keyboard method
- `mouse_move_distance` - Max pixels to move mouse
- `schedule_enabled` - Enable work schedule restrictions
- `work_hours_start` - Start time (24-hour format)
- `work_hours_end` - End time (24-hour format)
- `work_days` - Days to run (1=Monday, 7=Sunday)

### Mouse Automation (`config.json`)

```json
{
    "total_moves": 10,
    "move_duration": 2.0,
    "sleep_between_clicks": 5.0,
    "long_sleep_duration": 100.0,
    "left_click_coords": [1450, 80],
    "right_click_coords": [1450, 950],
    "jitter_range": 3,
    "duration_variation": 0.5
}
```

## Schedule Feature

The Activity Keeper includes smart scheduling to only run during configured work hours.

**Enable scheduling:**
```json
"schedule_enabled": true
```

**Example configurations:**

**Standard work hours (9-5, Mon-Fri):**
```json
"work_hours_start": "09:00",
"work_hours_end": "17:00",
"work_days": [1, 2, 3, 4, 5]
```

**Extended hours including weekends:**
```json
"work_hours_start": "08:00",
"work_hours_end": "20:00",
"work_days": [1, 2, 3, 4, 5, 6, 7]
```

**Behavior:**
- Program won't start if outside scheduled hours
- Automatically stops when schedule ends
- Shows schedule information on exit

## Features Breakdown

### Activity Keeper Dashboard

```
+------------------------------------------------+
|           TEAMS ACTIVITY KEEPER v2.0           |
+------------------------------------------------+
|  STATUS:    RUNNING                            |
|  UPTIME:    00:02:45                           |
|  INTERVAL:  120 s (Randomized)                 |
|  JIGGLES:   3                                  |
|  METHOD:    mouse                              |
+------------------------------------------------+
|     Press ESC or Q in this window to STOP      |
+------------------------------------------------+

Recent Activity:
[16:45:30] Heartbeat sent! (Moved -4, 7)
>>> NEXT HEARTBEAT IN: 115s
```

### Code Quality

This project follows professional Python coding standards:
- ✅ PEP8 style compliance
- ✅ Type hints for better code clarity
- ✅ Clear, descriptive function and variable names
- ✅ Modular design with single-responsibility functions
- ✅ Comprehensive error handling and logging
- ✅ Well-documented with docstrings

## Logging

Activity logs are saved to `activity_keeper.log` with timestamps and details of all activities performed.

## Safety Features

- **Failsafe**: Move mouse to any screen corner to emergency stop
- **Graceful shutdown**: Properly disables Stay Awake mode on exit
- **Keyboard interrupt**: Ctrl+C supported
- **Schedule enforcement**: Won't run outside configured hours

## Tips

1. **For Teams**: Use mouse method with default settings
2. **Prevent detection**: Enable schedule to match actual work hours
3. **Testing**: Use `--duration 60 --interval 10` for quick tests
4. **Backup**: The batch file runs from virtual environment automatically

## Troubleshooting

**"ModuleNotFoundError: No module named 'pyautogui'"**
- Activate virtual environment: `.venv\Scripts\activate`
- Install dependencies: `pip install pyautogui`

**Dashboard characters not displaying:**
- This has been fixed to use ASCII-compatible characters
- Should work in all Windows terminals

**Schedule not working:**
- Verify `schedule_enabled: true` in config
- Check time format is `"HH:MM"` (24-hour)
- Ensure work_days use 1-7 (1=Monday, 7=Sunday)

## License

This project is provided as-is for personal use.

## Author

**tatsuogoya**

## Acknowledgments

Built with Python and PyAutoGUI. Refactored following modern Python best practices.

---

**⚠️ Disclaimer**: This tool is for personal productivity. Use responsibly and in accordance with your organization's policies.

