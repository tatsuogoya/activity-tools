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
from datetime import datetime

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

EXIT_KEYS = [27, 81, 113]  # ESC, Q, q
JITTER_PERCENTAGE = 0.1
DASHBOARD_WIDTH = 48
VERBOSE = False  # Global verbose flag
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
    timestamp = time.strftime("%H:%M:%S")
    sys.stdout.write(f"[{timestamp}] {message}\n")
    sys.stdout.flush()


def verbose_log(message: str) -> None:
    """Print verbose message if verbose mode is enabled."""
    if VERBOSE:
        timestamp = time.strftime("%H:%M:%S")
        print(f"[VERBOSE {timestamp}] {message}")


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
            "work_days": [1, 2, 3, 4, 5]
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

def perform_activity(method: str, keyboard_key: str = "scrolllock", mouse_distance: int = 10) -> Tuple[int, int]:
    """Perform activity to keep system awake with randomization."""
    verbose_log(f"Performing activity: method={method}")
    dx, dy = 0, 0

    if method == "keyboard":
        pag.press(keyboard_key)
        logger.info(f"Pressed {keyboard_key} key")
    elif method == "mouse":
        # Randomize distance and direction
        dx = random.randint(-mouse_distance, mouse_distance)
        dy = random.randint(-mouse_distance, mouse_distance)

        # Ensure we actually move somewhere
        if dx == 0 and dy == 0:
            dx = 1

        # Move randomly and back
        pag.moveRel(dx, dy, duration=random.uniform(0.1, 0.3))
        time.sleep(random.uniform(0.05, 0.15))
        pag.moveRel(-dx, -dy, duration=random.uniform(0.1, 0.3))

        # Press F15 (Ghost Key) to ensure activity registration
        try:
            pag.press('f15')
        except Exception as e:
            logger.warning(f"Could not press F15 key: {e}")

        logger.info(f"Jiggled mouse ({dx}, {dy}) + F15 Key")

    return dx, dy


def draw_dashboard(status: str, interval: int, total_jiggles: int, start_time: float, method: str, activity_history: list) -> None:
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
    print(f"|{f'  STATUS:    {status}'.ljust(width)}|")
    print(f"|{f'  UPTIME:    {uptime_str}'.ljust(width)}|")
    print(f"|{f'  INTERVAL:  {interval} s (Randomized)'.ljust(width)}|")
    print(f"|{f'  JIGGLES:   {total_jiggles}'.ljust(width)}|")
    print(f"|{f'  METHOD:    {method}'.ljust(width)}|")
    print("+------------------------------------------------+")
    print(f"|{'Press ESC or Q in this window to STOP'.center(width)}|")
    print("+------------------------------------------------+")
    print("\nRecent Activity:")
    if activity_history:
        for activity in activity_history:
            print(activity)
    else:
        print("  No activities yet...")


def wait_for_next_activity(next_activity_time: float, end_time: float) -> bool:
    """Wait until next activity time. Returns False if user wants to exit."""
    last_printed_second = -1
    while time.time() < next_activity_time:
        # Check for exit key
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            verbose_log(f"Exit key detected: {key}")
            if key in EXIT_KEYS:
                return False

        # Calculate remaining time
        now = time.time()
        remaining_seconds = int(next_activity_time - now)

        if remaining_seconds != last_printed_second:
            display_sec = max(0, remaining_seconds)
            sys.stdout.write(f"\r>>> NEXT HEARTBEAT IN: {display_sec}s   ")
            sys.stdout.flush()
            last_printed_second = remaining_seconds

        time.sleep(0.1)
        if time.time() >= end_time:
            break
    return True


def keep_active(activity_interval: int, total_duration: int, method: str, keyboard_key: str, mouse_distance: int, config: dict) -> None:
    """Main function to keep the system active."""
    start_time = time.time()
    end_time = start_time + total_duration
    total_jiggles = 0
    activity_history = []  # Store last 5 activities

    # Enable Stay Awake Mode
    prevent_sleep()

    try:
        # Initial activity
        dx, dy = perform_activity(method, keyboard_key, mouse_distance)
        total_jiggles += 1

        # Add to history (keep last 5)
        timestamp = time.strftime("%H:%M:%S")
        activity_history.append(f"[{timestamp}] Heartbeat sent! (Moved {dx}, {dy})")
        if len(activity_history) > 5:
            activity_history.pop(0)

        while time.time() < end_time:
            # Check if still within schedule
            if not is_within_schedule(config):
                console_log("Outside scheduled hours. Stopping.")
                return
            
            # Draw UI
            draw_dashboard("RUNNING", activity_interval, total_jiggles, start_time, method, activity_history)

            # Clear any stray buffered key presses
            while msvcrt.kbhit():
                msvcrt.getch()

            # Randomize current interval jitter (±10%)
            jitter = int(activity_interval * JITTER_PERCENTAGE)
            current_wait = activity_interval + random.randint(-jitter, jitter)
            verbose_log(f"Next interval: {current_wait}s (jitter applied: ±{jitter}s)")

            next_activity_time = time.time() + current_wait

            if not wait_for_next_activity(next_activity_time, end_time):
                return

            if time.time() < end_time:
                dx, dy = perform_activity(method, keyboard_key, mouse_distance)
                total_jiggles += 1

                # Add to history (keep last 5)
                timestamp = time.strftime("%H:%M:%S")
                activity_history.append(f"[{timestamp}] Heartbeat sent! (Moved {dx}, {dy})")
                if len(activity_history) > 5:
                    activity_history.pop(0)

    except KeyboardInterrupt:
        print("\nActivity keeper stopped by user")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print(f"\nError: An unexpected error occurred")
        print(f"Details: {e}")
        print(f"Check {LOG_FILE} for more information.")
    finally:
        # Disable Stay Awake Mode so PC can sleep later
        allow_sleep()

        # Display session statistics
        display_exit_stats(start_time, total_jiggles)

        print("\nActivity keeper finished.")


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
    args = parser.parse_args()

    global VERBOSE, LOG_FILE, logger
    VERBOSE = args.verbose
    LOG_FILE = args.log

    # Setup logging with custom path
    setup_logging(LOG_FILE)
    logger = logging.getLogger(__name__)

    if VERBOSE:
        print(f"Teams Activity Keeper v{VERSION}")
        print("Verbose mode enabled - showing detailed output")
        verbose_log(f"Logging to: {LOG_FILE}")

    console_log(f"Teams Activity Keeper v{VERSION} starting...")

    config = load_config(args.config)

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

    # Check if within scheduled hours
    if not is_within_schedule(config):
        print("Outside scheduled hours. Exiting.")
        print(f"Schedule: {config.get('work_hours_start')} - {config.get('work_hours_end')}")
        print(f"Work days: {config.get('work_days')}")
        sys.exit(0)

    # Handle keyboard interrupt
    def signal_handler(sig: int, frame: object) -> None:
        logger.info("Script interrupted by user")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    keep_active(activity_interval, total_duration, method, keyboard_key, mouse_distance, config)


if __name__ == "__main__":
    main()
