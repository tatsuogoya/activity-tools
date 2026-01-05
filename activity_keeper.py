import sys
import time
import random
import argparse
import json
import os
import signal
import logging
import msvcrt
import ctypes
from typing import Optional, Tuple
from datetime import datetime, timedelta

try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

try:
    import pyautogui as pag
except ImportError:
    print("Error: pyautogui module not found!")
    print("Please install it with: pip install pyautogui")
    print("Or activate your virtual environment first.")
    sys.exit(1)

# Enable pyautogui failsafe
pag.FAILSAFE = True

# Windows API Constants for SetThreadExecutionState
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint),
                ("dwTime", ctypes.c_uint)]

def get_idle_time_seconds() -> float:
    """Returns the number of seconds since the last user input."""
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = ctypes.sizeof(LASTINPUTINFO)
    
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo)):
        millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
        return millis / 1000.0
    else:
        return 0.0

EXIT_KEYS = [27, 81, 113]  # ESC, Q, q
JITTER_PERCENTAGE = 0.1
DASHBOARD_WIDTH = 48
VERBOSE = False  # Global verbose flag
PAUSED = False  # Global pause state
DETECT_INACTIVITY = False # Global inactivity detection flag
AUTO_PAUSED = False # Global auto-paused state
RANDOM_PATTERN = False  # Global random pattern flag
QUIET = False  # Quiet/headless mode flag
DRY_RUN = False  # Dry-run mode flag (simulate activity)
AUTO_RESTART = False  # Auto-restart on schedule flag
PROFILE = "default"  # Current profile name
VERSION = "2.3.0"
LOG_FILE = "activity_keeper.log"
logger = None  # Will be initialized in main()

# Logger is now initialized in main() via setup_logging()


def setup_logging(log_file: str = 'activity_keeper.log') -> None:
    """Configure logging to specified file."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='a')
        ],
        force=True  # Reconfigure if already configured
    )


def console_log(message: str) -> None:
    """Print message to console with timestamp."""
    if not QUIET:
        timestamp = time.strftime("%H:%M:%S")
        sys.stdout.write(f"[{timestamp}] {message}\n")
        sys.stdout.flush()


def verbose_log(message: str) -> None:
    """Print verbose message if verbose mode is enabled."""
    if VERBOSE:
        timestamp = time.strftime("%H:%M:%S")
        print(f"[VERBOSE {timestamp}] {message}")


def play_sound(frequency: int = 1000, duration: int = 200) -> None:
    """Play a beep sound if sound is enabled and available."""
    if SOUND_AVAILABLE:
        try:
            winsound.Beep(frequency, duration)
        except Exception as e:
            verbose_log(f"Could not play sound: {e}")


def update_title(text: str) -> None:
    """Updates the console window title."""
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(text)
    except Exception:
        pass


def prevent_sleep() -> None:
    """Prevents Windows from going to sleep or turning off the screen."""
    verbose_log("Setting Windows Stay Awake mode")
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )
        msg = "Windows 'Stay Awake' mode enabled."
        logger.info(msg)
        console_log(msg)
    except Exception as e:
        logger.error(f"Failed to set execution state: {e}")


def allow_sleep() -> None:
    """Allows Windows to sleep normally again."""
    verbose_log("Disabling Windows Stay Awake mode")
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        msg = "Windows 'Stay Awake' mode disabled."
        logger.info(msg)
        console_log(msg)
    except Exception as e:
        logger.error(f"Failed to reset execution state: {e}")


def load_config(config_file: str = 'activity_config.json') -> dict:
    """Load configuration from JSON file."""
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {config_file}")
            print(f"Details: {e}")
            print("Please fix the JSON syntax and try again.")
            sys.exit(1)
        except Exception as e:
            print(f"Error: Could not read {config_file}")
            print(f"Details: {e}")
            sys.exit(1)
    else:
        # Default config
        console_log(f"Config file not found, using defaults")
        config = {
            "activity_interval": 120,
            "total_duration": 18000,
            "method": "mouse",
            "keyboard_key": "scrolllock",
            "mouse_move_distance": 10,
            "schedule_enabled": False,
            "work_hours_start": "09:00",
            "work_hours_end": "17:00",
            "work_days": [1, 2, 3, 4, 5],
            "schedule_warning_minutes": 5,
            "schedule_warning_sound": True,
            "sound_enabled": False,
            "sound_on_heartbeat": False,
            "sound_frequency": 1000,
            "sound_duration": 200,
            "inactivity_detection_enabled": False,
            "inactivity_threshold_seconds": 60,
            "inactivity_check_interval": 10,
            "pattern_randomization_enabled": False,
            "randomization_mouse_probability": 0.7
        }
    
    verbose_log(f"Loaded configuration from {config_file}")
    return config


def validate_config(config: dict) -> Tuple[bool, str]:
    """Validate configuration values. Returns (is_valid, error_message)."""
    verbose_log("Validating configuration")
    # Check activity_interval
    if config.get('activity_interval', 0) <= 0:
        return False, "Error: activity_interval must be positive (e.g., 120)"
    
    # Check total_duration
    if config.get('total_duration', 0) <= 0:
        return False, "Error: total_duration must be positive (e.g., 18000)"
    
    # Check mouse_move_distance
    if config.get('mouse_move_distance', 0) <= 0:
        return False, "Error: mouse_move_distance must be positive (e.g., 10)"
    
    # Check schedule time format if enabled
    if config.get('schedule_enabled', False):
        warning_minutes = config.get('schedule_warning_minutes', 5)
        if not isinstance(warning_minutes, (int, float)) or warning_minutes < 0:
            return False, "Error: schedule_warning_minutes must be >= 0 (e.g., 5)"

        try:
            from datetime import datetime
            datetime.strptime(config.get('work_hours_start', '09:00'), '%H:%M')
            datetime.strptime(config.get('work_hours_end', '17:00'), '%H:%M')
        except ValueError:
            return False, "Error: work_hours times must be in HH:MM format (e.g., '09:00')"
        
        # Check work_days
        work_days = config.get('work_days', [])
        if not work_days or not all(1 <= day <= 7 for day in work_days):
            return False, "Error: work_days must be list of numbers 1-7 (1=Monday, 7=Sunday)"
    
    # Check inactivity settings
    if config.get('inactivity_threshold_seconds', 60) <= 0:
        return False, "Error: inactivity_threshold_seconds must be positive"
    
    if config.get('inactivity_check_interval', 10) <= 0:
        return False, "Error: inactivity_check_interval must be positive"

    # Check pattern randomization settings
    if config.get('pattern_randomization_enabled', False):
        prob = config.get('randomization_mouse_probability', 0.7)
        if not (0.0 <= prob <= 1.0):
            return False, "Error: randomization_mouse_probability must be between 0.0 and 1.0"

    return True, ""


def save_config(config: dict, config_file: str = 'activity_config.json') -> None:
    """Save configuration to JSON file."""
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)


def is_within_schedule(config: dict) -> bool:
    """Check if current time is within configured schedule.
    
    Returns True if schedule is disabled or if current time/day matches schedule.
    work_days: 1=Monday, 7=Sunday
    """
    verbose_log(f"Checking schedule: enabled={config.get('schedule_enabled', False)}")
    if not config.get('schedule_enabled', False):
        return True
    
    now = datetime.now()
    
    # Check day of week
    if now.isoweekday() not in config.get('work_days', [1, 2, 3, 4, 5]):
        return False
    
    # Check time range
    start_time = datetime.strptime(config['work_hours_start'], '%H:%M').time()
    end_time = datetime.strptime(config['work_hours_end'], '%H:%M').time()
    current_time = now.time()
    
    return start_time <= current_time <= end_time


def get_next_schedule_start(config: dict) -> datetime:
    """Get the next datetime when the schedule will start."""
    now = datetime.now()

    if not config.get('schedule_enabled', False):
        return now

    if is_within_schedule(config):
        return now

    work_days = config.get('work_days', [1, 2, 3, 4, 5])
    start_time = datetime.strptime(config.get('work_hours_start', '09:00'), '%H:%M').time()

    if now.isoweekday() in work_days:
        today_start = datetime.combine(now.date(), start_time)
        if now < today_start:
            return today_start

    for day_offset in range(1, 8):
        candidate = now + timedelta(days=day_offset)
        if candidate.isoweekday() in work_days:
            return datetime.combine(candidate.date(), start_time)

    return now


def _get_schedule_end_timestamp(config: dict) -> Optional[float]:
    """Get today's schedule end time as a Unix timestamp, or None if not applicable."""
    if not config.get('schedule_enabled', False):
        return None

    now = datetime.now()
    if now.isoweekday() not in config.get('work_days', [1, 2, 3, 4, 5]):
        return None

    try:
        end_time = datetime.strptime(config.get('work_hours_end', '17:00'), '%H:%M').time()
    except ValueError:
        return None

    end_dt = datetime.combine(now.date(), end_time)
    return end_dt.timestamp()


def check_schedule_warning(config: dict, warning_shown: bool) -> Tuple[bool, bool]:
    """Check if schedule is ending soon and should trigger a one-time warning.

    Returns (should_warn_now, new_warning_shown).
    """
    schedule_end_ts = _get_schedule_end_timestamp(config)
    if schedule_end_ts is None:
        return False, warning_shown

    warning_minutes = config.get('schedule_warning_minutes', 5)
    try:
        warning_minutes = float(warning_minutes)
    except (TypeError, ValueError):
        warning_minutes = 5

    if warning_minutes <= 0:
        return False, warning_shown

    seconds_remaining = schedule_end_ts - time.time()
    minutes_remaining = seconds_remaining / 60.0

    if 0 < minutes_remaining <= warning_minutes and not warning_shown:
        return True, True

    return False, warning_shown

def perform_activity(method: str, keyboard_key: str = "scrolllock", mouse_distance: int = 10, pattern_randomization_enabled: bool = False, mouse_probability: float = 0.7) -> Tuple[int, int]:
    """Perform activity to keep system awake with randomization."""
    
    # Handle pattern randomization
    if RANDOM_PATTERN or pattern_randomization_enabled:
        original_method = method
        if random.random() < mouse_probability:
            method = "mouse"
        else:
            method = "keyboard"
        verbose_log(f"Random pattern: selected {method} method (original: {original_method})")

    verbose_log(f"Performing activity: method={method}")
    dx, dy = 0, 0

    if method == "keyboard":
        if DRY_RUN:
            verbose_log(f"DRY-RUN: Would have pressed {keyboard_key} key")
        else:
            pag.press(keyboard_key)
        logger.info(f"Pressed {keyboard_key} key (DRY-RUN: {DRY_RUN})")
    elif method == "mouse":
        # Randomize distance and direction
        dx = random.randint(-mouse_distance, mouse_distance)
        dy = random.randint(-mouse_distance, mouse_distance)

        # Ensure we actually move somewhere
        if dx == 0 and dy == 0:
            dx = 1

        if DRY_RUN:
            verbose_log(f"DRY-RUN: Would have moved mouse ({dx}, {dy})")
            # Simulate timing
            time.sleep(random.uniform(0.1, 0.3))
            time.sleep(random.uniform(0.05, 0.15))
            time.sleep(random.uniform(0.1, 0.3))
            verbose_log("DRY-RUN: Would have pressed F15 key")
        else:
            # Move randomly and back
            pag.moveRel(dx, dy, duration=random.uniform(0.1, 0.3))
            time.sleep(random.uniform(0.05, 0.15))
            pag.moveRel(-dx, -dy, duration=random.uniform(0.1, 0.3))

            # Press F15 (Ghost Key) to ensure activity registration
            try:
                pag.press('f15')
            except Exception as e:
                logger.warning(f"Could not press F15 key: {e}")

        logger.info(f"Jiggled mouse ({dx}, {dy}) + F15 Key (DRY-RUN: {DRY_RUN})")

    return dx, dy


def draw_dashboard(status: str, interval: int, total_jiggles: int, start_time: float, method: str, activity_history: list, show_warning: bool = False, waiting_until: Optional[datetime] = None) -> None:
    """Draws a clean, persistent dashboard in the console."""
    uptime_sec = int(time.time() - start_time)
    hours, remainder = divmod(uptime_sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # Internal width of the box
    width = DASHBOARD_WIDTH
 
    if not VERBOSE:
        os.system('cls' if os.name == 'nt' else 'clear')
    else:
        print("\n--- DASHBOARD UPDATE ---")

    print("+------------------------------------------------+")
    print(f"|{f'TEAMS ACTIVITY KEEPER v{VERSION}'.center(width)}|")
    print("+------------------------------------------------+")
    if PAUSED:
        status_display = f"{status} (PAUSED)" if status == "WAITING" else "PAUSED"
    else:
        status_display = status
    if DRY_RUN:
        status_display += " [DRY-RUN]"
    print(f"|{f'  STATUS:    {status_display}'.ljust(width)}|")
    print(f"|{f'  UPTIME:    {uptime_str}'.ljust(width)}|")
    print(f"|{f'  INTERVAL:  {interval} s (Randomized)'.ljust(width)}|")
    print(f"|{f'  JIGGLES:   {total_jiggles}'.ljust(width)}|")
    print(f"|{f'  METHOD:    {method}'.ljust(width)}|")
    if PROFILE != "default":
        print(f"|{f'  PROFILE:   {PROFILE}'.ljust(width)}|")
    if DETECT_INACTIVITY:
        inactivity_status = "ENABLED"
        if AUTO_PAUSED:
            inactivity_status += " (AUTO-PAUSED)"
        print(f"|{f'  INACTIVITY:{inactivity_status}'.ljust(width)}|")
    if waiting_until is not None:
        resumes_at = waiting_until.strftime("%A %H:%M")
        seconds_left = max(0, int(waiting_until.timestamp() - time.time()))
        hours_left, remainder = divmod(seconds_left, 3600)
        minutes_left, seconds_left = divmod(remainder, 60)
        print(f"|{f'  RESUMES:   {resumes_at}'.ljust(width)}|")
        print(f"|{f'  STARTS IN: {hours_left:02d}:{minutes_left:02d}:{seconds_left:02d}'.ljust(width)}|")
    if show_warning:
        print(f"|{f'  WARNING: Schedule ending soon!'.ljust(width)}|")
    print("+------------------------------------------------+")
    print(f"|{'Press ESC/Q=STOP | P=PAUSE | R=RESUME'.center(width)}|")
    print("+------------------------------------------------+")
    print("\nRecent Activity:")
    if activity_history:
        for activity in activity_history:
            print(activity)
    else:
        print("  No activities yet...")


def wait_for_next_activity(next_activity_time: float, end_time: float, config: dict = None) -> bool:
    """Wait until next activity time. Returns False if user wants to exit."""
    global PAUSED, AUTO_PAUSED
    if PAUSED and not AUTO_PAUSED:
        return True
        
    # Check for inactivity detection logic
    check_inactivity = DETECT_INACTIVITY or (config and config.get('inactivity_detection_enabled', False))
    inactivity_threshold = config.get('inactivity_threshold_seconds', 60) if config else 60

    last_printed_second = -1
    while time.time() < next_activity_time:
        # Check for inactivity
        if check_inactivity:
            idle_time = get_idle_time_seconds()
            
            # Auto-pause if user is active
            if idle_time < inactivity_threshold:
                if not PAUSED:
                    PAUSED = True
                    AUTO_PAUSED = True
                    console_log("User activity detected, automatically pausing...")
                    verbose_log(f"Auto-pausing: idle_time={idle_time:.2f}s < threshold={inactivity_threshold}s")
                    return True # Return to main loop to handle pause state
            
            # Auto-resume if user is inactive and was auto-paused
            elif PAUSED and AUTO_PAUSED:
                if idle_time >= inactivity_threshold:
                    PAUSED = False
                    AUTO_PAUSED = False
                    console_log("User inactivity detected, automatically resuming...")
                    verbose_log(f"Auto-resuming: idle_time={idle_time:.2f}s >= threshold={inactivity_threshold}s")

        # Check for exit/pause/resume keys
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key in EXIT_KEYS:
                verbose_log(f"Exit key detected: {key}")
                return False
            if key in [80, 112]:  # P or p
                PAUSED = True
                AUTO_PAUSED = False # Manual pause overrides auto-pause
                verbose_log("Program PAUSED")
                return True
            if key in [82, 114]:  # R or r
                PAUSED = False
                AUTO_PAUSED = False
                verbose_log("Program RESUMED")

        # Calculate remaining time
        now = time.time()
        remaining_seconds = int(next_activity_time - now)

        if remaining_seconds != last_printed_second:
            if not QUIET:
                display_sec = max(0, remaining_seconds)
                sys.stdout.write(f"\r>>> NEXT HEARTBEAT IN: {display_sec}s   ")
                if VERBOSE and check_inactivity:
                     sys.stdout.write(f"(Idle: {get_idle_time_seconds():.1f}s)   ")
                sys.stdout.flush()
            last_printed_second = remaining_seconds

        time.sleep(0.1)
        if time.time() >= end_time:
            break
    return True


def handle_pause_resume() -> None:
    """Check for pause/resume keys and update state."""
    global PAUSED
    if msvcrt.kbhit():
        key = ord(msvcrt.getch())
        if key in [80, 112]:  # P or p
            PAUSED = True
            verbose_log("Program PAUSED")
        elif key in [82, 114]:  # R or r
            PAUSED = False
            AUTO_PAUSED = False  # Reset auto-pause on manual resume
            verbose_log("Program RESUMED")


def keep_active(activity_interval: int, total_duration: int, method: str, keyboard_key: str, mouse_distance: int, config: dict) -> Tuple[bool, int]:
    """Main function to keep the system active.

    Returns (should_wait_for_schedule, session_jiggles).
    """
    global PAUSED, AUTO_PAUSED
    start_time = time.time()
    end_time = start_time + total_duration
    total_jiggles = 0
    activity_history = []  # Store last 5 activities
    warning_shown = False
    should_wait_for_schedule = False

    # Extract randomization settings
    pattern_randomization_enabled = config.get('pattern_randomization_enabled', False)
    mouse_probability = config.get('randomization_mouse_probability', 0.7)

    # Enable Stay Awake Mode
    prevent_sleep()

    if config.get('sound_enabled', False):
        play_sound(config.get('sound_frequency', 1000), config.get('sound_duration', 200))
        verbose_log("Played startup sound")

    try:
        # Check for initial inactivity pause
        check_inactivity = DETECT_INACTIVITY or config.get('inactivity_detection_enabled', False)
        if check_inactivity:
            idle_time = get_idle_time_seconds()
            inactivity_threshold = config.get('inactivity_threshold_seconds', 60)
            if idle_time < inactivity_threshold:
                 PAUSED = True
                 AUTO_PAUSED = True
                 console_log("User activity detected, automatically pausing...")
                 verbose_log(f"Auto-pausing on start: idle_time={idle_time:.2f}s < threshold={inactivity_threshold}s")

        # Initial activity (only if not paused)
        if not PAUSED:
            dx, dy = perform_activity(method, keyboard_key, mouse_distance, pattern_randomization_enabled, mouse_probability)
            total_jiggles += 1

            # Sound notification
            if config.get('sound_enabled', False) and config.get('sound_on_heartbeat', False):
                play_sound(config.get('sound_frequency', 1000), config.get('sound_duration', 200))

            # Add to history (keep last 5)
            timestamp = time.strftime("%H:%M:%S")
            activity_history.append(f"[{timestamp}] Heartbeat sent! (Moved {dx}, {dy})")
            if len(activity_history) > 5:
                activity_history.pop(0)

        while time.time() < end_time:
            # Check if still within schedule
            if not is_within_schedule(config):
                if AUTO_RESTART and config.get('schedule_enabled', False):
                    console_log("Outside scheduled hours. Entering waiting mode.")
                    logger.info("Outside work hours, returning to waiting mode")
                    should_wait_for_schedule = True
                    return True, total_jiggles

                console_log("Outside scheduled hours. Stopping.")
                return False, total_jiggles

            # Check for schedule warning
            should_warn, warning_shown = check_schedule_warning(config, warning_shown)
            if should_warn:
                warning_minutes = config.get('schedule_warning_minutes', 5)
                console_log(
                    f"WARNING: Schedule will end in less than {warning_minutes} minutes!"
                )
                logger.warning(
                    f"Schedule ending soon (threshold: {warning_minutes} minutes)"
                )
                if config.get('schedule_warning_sound', True) and config.get('sound_enabled', False):
                    play_sound(1500, 500)
                    play_sound(1500, 500)
            
            # Draw UI
            if not QUIET:
                draw_dashboard(
                    "RUNNING",
                    activity_interval,
                    total_jiggles,
                    start_time,
                    method,
                    activity_history,
                    warning_shown,
                )

            # Handle buffered key presses (exit/pause/resume)
            while msvcrt.kbhit():
                key = ord(msvcrt.getch())
                if key in EXIT_KEYS:
                    return False, total_jiggles
                if key in [80, 112]:  # P or p
                    PAUSED = True
                    verbose_log("Program PAUSED")
                elif key in [82, 114]:  # R or r
                    PAUSED = False
                    AUTO_PAUSED = False  # Reset auto-pause on manual resume
                    verbose_log("Program RESUMED")

            # Randomize current interval jitter (±10%)
            jitter = int(activity_interval * JITTER_PERCENTAGE)
            current_wait = activity_interval + random.randint(-jitter, jitter)
            verbose_log(f"Next interval: {current_wait}s (jitter applied: ±{jitter}s)")

            next_activity_time = time.time() + current_wait

            if not wait_for_next_activity(next_activity_time, end_time, config):
                return False, total_jiggles

            # While paused, update dashboard more frequently
            while PAUSED and time.time() < end_time:
                # Check for inactivity auto-resume
                check_inactivity = DETECT_INACTIVITY or config.get('inactivity_detection_enabled', False)
                if check_inactivity and AUTO_PAUSED:
                    idle_time = get_idle_time_seconds()
                    inactivity_threshold = config.get('inactivity_threshold_seconds', 60)
                    
                    if idle_time >= inactivity_threshold:
                        PAUSED = False
                        AUTO_PAUSED = False
                        console_log("User inactivity detected, automatically resuming...")
                        verbose_log(f"Auto-resuming: idle_time={idle_time:.2f}s >= threshold={inactivity_threshold}s")
                        break
                
                if not is_within_schedule(config):
                    if AUTO_RESTART and config.get('schedule_enabled', False):
                        console_log("Outside scheduled hours. Entering waiting mode.")
                        logger.info("Outside work hours, returning to waiting mode")
                        should_wait_for_schedule = True
                        return True, total_jiggles

                    console_log("Outside scheduled hours. Stopping.")
                    return False, total_jiggles

                should_warn, warning_shown = check_schedule_warning(config, warning_shown)
                if should_warn:
                    warning_minutes = config.get('schedule_warning_minutes', 5)
                    console_log(
                        f"WARNING: Schedule will end in less than {warning_minutes} minutes!"
                    )
                    logger.warning(
                        f"Schedule ending soon (threshold: {warning_minutes} minutes)"
                    )
                    if config.get('schedule_warning_sound', True) and config.get('sound_enabled', False):
                        play_sound(1500, 500)
                        play_sound(1500, 500)

                if not QUIET:
                    draw_dashboard(
                        "RUNNING",
                        activity_interval,
                        total_jiggles,
                        start_time,
                        method,
                        activity_history,
                        warning_shown,
                    )

                if msvcrt.kbhit():
                    key = ord(msvcrt.getch())
                    if key in EXIT_KEYS:
                        return False, total_jiggles
                    elif key in [82, 114]:  # R or r
                        PAUSED = False
                        AUTO_PAUSED = False # Reset auto-pause
                        verbose_log("Program RESUMED")
                    elif key in [80, 112]:  # P or p
                        PAUSED = True
                        AUTO_PAUSED = False # Manual pause overrides auto-pause
                        verbose_log("Program PAUSED")

                time.sleep(0.5)

            if time.time() < end_time and not PAUSED:
                dx, dy = perform_activity(method, keyboard_key, mouse_distance, pattern_randomization_enabled, mouse_probability)
                total_jiggles += 1

                # Sound notification
                if config.get('sound_enabled', False) and config.get('sound_on_heartbeat', False):
                    play_sound(config.get('sound_frequency', 1000), config.get('sound_duration', 200))

                # Add to history (keep last 5)
                timestamp = time.strftime("%H:%M:%S")
                activity_history.append(f"[{timestamp}] Heartbeat sent! (Moved {dx}, {dy})")
                if len(activity_history) > 5:
                    activity_history.pop(0)

        return False, total_jiggles

    except KeyboardInterrupt:
        print("\nActivity keeper stopped by user")
        return False, total_jiggles
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print(f"\nError: An unexpected error occurred")
        print(f"Details: {e}")
        print(f"Check {LOG_FILE} for more information.")
        return False, total_jiggles
    finally:
        # Disable Stay Awake Mode so PC can sleep later
        allow_sleep()

        if config.get('sound_enabled', False) and not should_wait_for_schedule:
            play_sound(800, 300)  # Lower frequency, longer duration for exit
            verbose_log("Played exit sound")


def display_exit_stats(start_time: float, total_jiggles: int) -> None:
    """Display statistics when program exits."""
    total_runtime = time.time() - start_time
    hours, remainder = divmod(int(total_runtime), 3600)
    minutes, seconds = divmod(remainder, 60)

    print("\n" + "=" * 50)
    print("SESSION STATISTICS")
    print("=" * 50)
    print(f"Total Runtime:    {hours:02d}:{minutes:02d}:{seconds:02d}")
    print(f"Total Jiggles:    {total_jiggles}")

    avg_interval = None
    if total_jiggles > 1:
        avg_interval = total_runtime / (total_jiggles - 1)
        print(f"Average Interval: {avg_interval:.1f} seconds")

    print("=" * 50)

    runtime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    if avg_interval is not None:
        logger.info(
            f"Session ended - Runtime: {runtime_str}, "
            f"Jiggles: {total_jiggles}, Avg Interval: {avg_interval:.1f}s"
        )
    else:
        logger.info(f"Session ended - Runtime: {runtime_str}, Jiggles: {total_jiggles}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Keep PC active and Teams green without mouse clicks")
    parser.add_argument('--config', type=str, default='activity_config.json', help='Configuration file')
    parser.add_argument('--interval', type=int, help='Activity interval in seconds')
    parser.add_argument('--duration', type=int, help='Total duration in seconds')
    parser.add_argument('--method', choices=['keyboard', 'mouse'], help='Activity method')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output with detailed information')
    parser.add_argument('--version', action='version', version=f'Teams Activity Keeper v{VERSION}')
    parser.add_argument('--log', type=str, default='activity_keeper.log', help='Path to log file (default: activity_keeper.log)')
    parser.add_argument('--profile', type=str, help='Profile name (e.g., work, home) - loads {profile}_config.json')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode - no dashboard, logs only')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (simulate activity without actually moving mouse/keyboard)')
    parser.add_argument('--auto-restart', action='store_true', help='Automatically wait and restart when schedule begins (instead of exiting)')
    parser.add_argument('--detect-inactivity', action='store_true', help='Automatically pause when user activity is detected')
    parser.add_argument('--random-pattern', action='store_true', help='Randomly vary activity method between mouse and keyboard for human-like behavior')
    args = parser.parse_args()

    global VERBOSE, LOG_FILE, logger, PROFILE, QUIET, DRY_RUN, AUTO_RESTART, PAUSED, DETECT_INACTIVITY, AUTO_PAUSED, RANDOM_PATTERN
    VERBOSE = args.verbose
    LOG_FILE = args.log
    QUIET = args.quiet
    DRY_RUN = args.dry_run
    AUTO_RESTART = args.auto_restart
    DETECT_INACTIVITY = args.detect_inactivity
    RANDOM_PATTERN = args.random_pattern
    
    if QUIET:
        print("Quiet mode enabled - running in background")
    
    if DRY_RUN:
        print("DRY-RUN mode enabled - simulating activity")

    if args.profile:
        PROFILE = args.profile

    # Setup logging with custom path
    setup_logging(LOG_FILE)
    logger = logging.getLogger(__name__)

    if VERBOSE:
        print(f"Teams Activity Keeper v{VERSION}")
        print("Verbose mode enabled - showing detailed output")
        verbose_log(f"Logging to: {LOG_FILE}")

    if PROFILE != "default":
        console_log(f"Teams Activity Keeper v{VERSION} [{PROFILE} profile] starting...")
    else:
        console_log(f"Teams Activity Keeper v{VERSION} starting...")

    # Determine config file based on profile
    if args.profile and args.config == 'activity_config.json':
        # Profile specified and no explicit config file
        config_file = f"{args.profile}_config.json"
        if not os.path.exists(config_file):
            print(f"Warning: Profile config '{config_file}' not found, using default.")
            config_file = 'activity_config.json'
    else:
        config_file = args.config
    
    if VERBOSE:
        verbose_log(f"Using profile: {PROFILE}")
        verbose_log(f"Loading config: {config_file}")
    
    config = load_config(config_file)

    # Validate configuration
    is_valid, error_msg = validate_config(config)
    if not is_valid:
        print(error_msg)
        print("Please check your configuration file and try again.")
        sys.exit(1)

    # Override config with command line args if provided
    activity_interval = args.interval or config.get('activity_interval', 120)
    total_duration = args.duration or config.get('total_duration', 18000)
    method = args.method or config.get('method', 'mouse')
    keyboard_key = config.get('keyboard_key', 'scrolllock')
    mouse_distance = config.get('mouse_move_distance', 10)

    if VERBOSE:
        print(f"Configuration: interval={activity_interval}s, duration={total_duration}s, method={method}")

    # Handle keyboard interrupt
    def signal_handler(sig: int, frame: object) -> None:
        logger.info("Script interrupted by user")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    program_start_time = time.time()
    program_total_jiggles = 0

    try:
        while True:
            if config.get('schedule_enabled', False) and not is_within_schedule(config):
                if not AUTO_RESTART:
                    print("Outside scheduled hours. Exiting.")
                    print(f"Schedule: {config.get('work_hours_start')} - {config.get('work_hours_end')}")
                    print(f"Work days: {config.get('work_days')}")
                    sys.exit(0)

                next_start = get_next_schedule_start(config)
                logger.info(
                    f"Outside work hours, waiting for next schedule (resumes at {next_start.strftime('%H:%M')})"
                )
                console_log(
                    f"Outside work hours, waiting for next schedule (resumes at {next_start.strftime('%H:%M on %A')})"
                )

                while config.get('schedule_enabled', False) and not is_within_schedule(config):
                    next_start = get_next_schedule_start(config)
                    if not QUIET:
                        draw_dashboard(
                            "WAITING",
                            activity_interval,
                            program_total_jiggles,
                            program_start_time,
                            method,
                            [],
                            show_warning=False,
                            waiting_until=next_start,
                        )

                    for _ in range(60):
                        if msvcrt.kbhit():
                            key = ord(msvcrt.getch())
                            if key in EXIT_KEYS:
                                return
                            if key in [80, 112]:  # P or p
                                PAUSED = True
                                verbose_log("Program PAUSED")
                            elif key in [82, 114]:  # R or r
                                PAUSED = False
                                AUTO_PAUSED = False  # Reset auto-pause on manual resume
                                verbose_log("Program RESUMED")

                        if is_within_schedule(config):
                            break
                        time.sleep(1)

                logger.info("Schedule started, resuming activity")
                console_log("Schedule started, resuming activity")
                continue

            should_wait_for_schedule, session_jiggles = keep_active(
                activity_interval,
                total_duration,
                method,
                keyboard_key,
                mouse_distance,
                config,
            )
            program_total_jiggles += session_jiggles

            if should_wait_for_schedule and AUTO_RESTART:
                continue

            break
    finally:
        display_exit_stats(program_start_time, program_total_jiggles)
        print("\nActivity keeper finished.")


if __name__ == "__main__":
    main()
