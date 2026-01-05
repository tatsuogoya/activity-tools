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
- 🔄 Auto-restart mode (waits for schedule and resumes automatically)
- 🧪 Dry-run mode (simulate activity without actual input)
- 🎯 Stay Awake mode (prevents Windows sleep)
- 📊 Real-time dashboard with activity history (last 5 heartbeats)
- 📈 Exit statistics (runtime, total jiggles, average interval)
- 🔍 Verbose mode for debugging
- 🔑 Ghost key (F15) for activity registration
- 🛡️ Failsafe support (move mouse to corner to stop)
- ⚙️ Config validation with helpful error messages
- 📝 Custom log file path support
- 🏷️ Version display
- 🎵 Sound notifications (startup, heartbeat, exit, warnings)
- ⏰ Countdown warnings before schedule ends
- 🤫 Quiet/headless mode for background operation
- 👤 Multiple profile support
- ⏸️ Pause/Resume functionality

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
- `--verbose` - Enable verbose output with detailed debugging information
- `--version` - Display version and exit
- `--log` - Custom log file path (default: `activity_keeper.log`)
- `--profile` - Load profile-specific config (e.g., `work` loads `work_config.json`)
- `--quiet` - Run in quiet mode (no dashboard, logs only)
- `--dry-run` - Simulate activity without actually moving mouse/keyboard
- `--auto-restart` - Automatically wait and restart when schedule begins (instead of exiting)

**Interactive controls:**
- Press **ESC** or **Q** to stop the program
- Press **P** to pause the program
- Press **R** to resume the program
- Dashboard updates in real-time
- Countdown shows time until next activity

### Dry-Run Mode

Use the `--dry-run` flag to simulate activity without actually performing any mouse movements or key presses.

**Use Cases:**
- **Testing Configurations:** Verify your schedule and interval settings without triggering actual inputs.
- **Previewing Behavior:** Watch the dashboard to see when activities would occur.
- **Debugging:** Troubleshoot issues without affecting your system state.

In dry-run mode, the dashboard will show `[DRY-RUN]` in the status line, and all actions will be logged to the console/log file as simulations.

**Example:**
```bash
python activity_keeper.py --dry-run --verbose --duration 60
```

### Auto-Restart Mode

Use the `--auto-restart` flag to keep the script running even when outside work hours. It will automatically resume when the schedule begins.

**Use Cases:**
- **Set-and-Forget Operation:** Run overnight or over weekends without manual restart.
- **Automatic Across Schedule Boundaries:** Perfect for flexible work schedules.
- **Background Mode:** Combine with `--quiet` for fully automated operation.

When waiting for schedule, the dashboard shows:
- **Status:** `WAITING`
- **Resume Time:** "RESUMES: Monday 09:00"
- **Countdown:** "STARTS IN: 15:23:45"

**Example:**
```bash
# Run continuously, waiting for work hours
python activity_keeper.py --auto-restart --schedule

# Combine with quiet mode for background operation
python activity_keeper.py --auto-restart --quiet
```

**Note:** Without `--auto-restart`, the script will exit when outside scheduled hours (default behavior).

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
    "work_days": [1, 2, 3, 4, 5],
    "schedule_warning_minutes": 5,
    "schedule_warning_sound": true,
    "sound_enabled": false,
    "sound_on_heartbeat": false,
    "sound_frequency": 1000,
    "sound_duration": 200
}
```

**Configuration options:**

**Basic Settings:**
- `activity_interval` - Seconds between activities (randomized ±10%)
- `total_duration` - How long to run (in seconds)
- `method` - `"mouse"` or `"keyboard"`
- `keyboard_key` - Key to press for keyboard method
- `mouse_move_distance` - Max pixels to move mouse

**Schedule Settings:**
- `schedule_enabled` - Enable work schedule restrictions
- `work_hours_start` - Start time (24-hour format, e.g., "09:00")
- `work_hours_end` - End time (24-hour format, e.g., "17:00")
- `work_days` - Days to run (1=Monday, 7=Sunday)
- `schedule_warning_minutes` - Minutes before schedule ends to show warning (default: 5)
- `schedule_warning_sound` - Play sound when schedule ending warning appears

**Sound Settings:**
- `sound_enabled` - Enable all sound notifications
- `sound_on_heartbeat` - Play sound on each activity heartbeat
- `sound_frequency` - Sound frequency in Hz (default: 1000)
- `sound_duration` - Sound duration in milliseconds (default: 200)

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
- Without `--auto-restart`: Program won't start if outside scheduled hours, exits when schedule ends
- With `--auto-restart`: Program waits for schedule to begin, automatically resumes when schedule starts
- Automatically stops when schedule ends (or re-enters waiting mode with auto-restart)
- Shows schedule information and warnings
- Countdown warnings can alert you X minutes before schedule ends

## Advanced Features

### Multiple Profiles

Use the `--profile` flag to switch between different configurations for different scenarios.

**Example:**
```bash
# Create work_config.json for work hours
python activity_keeper.py --profile work

# Create home_config.json for personal use
python activity_keeper.py --profile home
```

The script will load `{profile}_config.json`. If not found, it falls back to `activity_config.json`.

### Pause/Resume

Press **P** to pause activity at any time. The dashboard will show "PAUSED" status.
Press **R** to resume. This works even in waiting mode.

### Sound Notifications

Enable sound notifications in your config:
```json
{
    "sound_enabled": true,
    "sound_on_heartbeat": false,
    "sound_frequency": 1000,
    "sound_duration": 200
}
```

Sounds play on:
- Startup
- Each heartbeat (if `sound_on_heartbeat` is true)
- Exit
- Schedule ending warnings (double beep)

### Quiet Mode

Use `--quiet` to run in headless mode with no dashboard output:
```bash
python activity_keeper.py --quiet --auto-restart
```

Perfect for:
- Running as a background process
- Minimizing console distractions
- Logging-only operation

## Features Breakdown

### Activity Keeper Dashboard

**Running Mode:**
```
+------------------------------------------------+
|          TEAMS ACTIVITY KEEPER v2.3.0          |
+------------------------------------------------+
|  STATUS:    RUNNING                            |
|  UPTIME:    00:02:45                           |
|  INTERVAL:  120 s (Randomized)                 |
|  JIGGLES:   5                                  |
|  METHOD:    mouse                              |
+------------------------------------------------+
|     Press ESC/Q=STOP | P=PAUSE | R=RESUME      |
+------------------------------------------------+

Recent Activity:
[16:40:12] Heartbeat sent! (Moved 3, -5)
[16:42:15] Heartbeat sent! (Moved -2, 7)
[16:44:20] Heartbeat sent! (Moved 4, 1)
[16:46:25] Heartbeat sent! (Moved -6, -3)
[16:48:30] Heartbeat sent! (Moved 2, 8)
>>> NEXT HEARTBEAT IN: 115s
```

**Waiting Mode (with --auto-restart):**
```
+------------------------------------------------+
|          TEAMS ACTIVITY KEEPER v2.3.0          |
+------------------------------------------------+
|  STATUS:    WAITING [DRY-RUN]                  |
|  UPTIME:    00:05:30                           |
|  INTERVAL:  120 s (Randomized)                 |
|  JIGGLES:   0                                  |
|  METHOD:    mouse                              |
|  RESUMES:   Monday 09:00                       |
|  STARTS IN: 03:24:30                           |
+------------------------------------------------+
|     Press ESC/Q=STOP | P=PAUSE | R=RESUME      |
+------------------------------------------------+

Recent Activity:
  No activities yet...
```

### Exit Statistics

When the program stops, it displays a summary:
```
==================================================
SESSION STATISTICS
==================================================
Total Runtime:    02:15:30
Total Jiggles:    68
Average Interval: 120.3 seconds
==================================================
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
3. **Testing**: Use `--dry-run --duration 60 --interval 10` for quick tests without actual activity
4. **Backup**: The batch file runs from virtual environment automatically
5. **Overnight Operation**: Use `--auto-restart --quiet` to run continuously in background
6. **Multiple Scenarios**: Create different profiles (work, home, test) with separate configs
7. **Debugging**: Enable `--verbose` to see detailed logs of all operations
8. **Sound Alerts**: Enable schedule warnings to get notified before work hours end

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

