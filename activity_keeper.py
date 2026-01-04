import pyautogui as pag
import time
import random
import argparse
import json
import os
import signal
import sys
import logging
import msvcrt
import ctypes
from typing import Optional, Tuple
from datetime import datetime

# Enable pyautogui failsafe
pag.FAILSAFE = True

# Windows API Constants for SetThreadExecutionState
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

EXIT_KEYS = [27, 81, 113]  # ESC, Q, q
JITTER_PERCENTAGE = 0.1
DASHBOARD_WIDTH = 48

# Configure logging to file only (to prevent interference with console dashboard)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('activity_keeper.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


def console_log(message: str) -> None:
    """Print message to console with timestamp."""
    timestamp = time.strftime("%H:%M:%S")
    sys.stdout.write(f"[{timestamp}] {message}\n")
    sys.stdout.flush()


def update_title(text: str) -> None:
    """Updates the console window title."""
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(text)
    except Exception:
        pass


def prevent_sleep() -> None:
    """Prevents Windows from going to sleep or turning off the screen."""
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
        with open(config_file, 'r') as f:
            return json.load(f)
    else:
        # Default config
        return {
            "activity_interval": 120,  # 2 minutes
            "total_duration": 18000,   # 5 hours
            "method": "mouse",         # "keyboard" or "mouse"
            "keyboard_key": "scrolllock",
            "mouse_move_distance": 10
        }


def save_config(config: dict, config_file: str = 'activity_config.json') -> None:
    """Save configuration to JSON file."""
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)


def is_within_schedule(config: dict) -> bool:
    """Check if current time is within configured schedule.
    
    Returns True if schedule is disabled or if current time/day matches schedule.
    work_days: 1=Monday, 7=Sunday
    """
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


def draw_dashboard(status: str, interval: int, total_jiggles: int, start_time: float, method: str) -> None:
    """Draws a clean, persistent dashboard in the console."""
    uptime_sec = int(time.time() - start_time)
    hours, remainder = divmod(uptime_sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # Internal width of the box
    width = DASHBOARD_WIDTH

    os.system('cls' if os.name == 'nt' else 'clear')
    print("+------------------------------------------------+")
    print(f"|{'TEAMS ACTIVITY KEEPER v2.0'.center(width)}|")
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


def wait_for_next_activity(next_activity_time: float, end_time: float) -> bool:
    """Wait until next activity time. Returns False if user wants to exit."""
    last_printed_second = -1
    while time.time() < next_activity_time:
        # Check for exit key
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
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

    # Enable Stay Awake Mode
    prevent_sleep()

    try:
        # Initial activity
        dx, dy = perform_activity(method, keyboard_key, mouse_distance)
        total_jiggles += 1

        while time.time() < end_time:
            # Check if still within schedule
            if not is_within_schedule(config):
                console_log("Outside scheduled hours. Stopping.")
                return
            
            # Draw UI
            draw_dashboard("RUNNING", activity_interval, total_jiggles, start_time, method)
            if total_jiggles > 0:
                ts = time.strftime("%H:%M:%S")
                print(f"[{ts}] Heartbeat sent! (Moved {dx}, {dy})")

            # Clear any stray buffered key presses
            while msvcrt.kbhit():
                msvcrt.getch()

            # Randomize current interval jitter (±10%)
            jitter = int(activity_interval * JITTER_PERCENTAGE)
            current_wait = activity_interval + random.randint(-jitter, jitter)

            next_activity_time = time.time() + current_wait

            if not wait_for_next_activity(next_activity_time, end_time):
                return

            if time.time() < end_time:
                dx, dy = perform_activity(method, keyboard_key, mouse_distance)
                total_jiggles += 1

    except KeyboardInterrupt:
        print("Activity keeper stopped by user")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print(f"Error: {e}")
    finally:
        # Disable Stay Awake Mode so PC can sleep later
        allow_sleep()
        print("\nActivity keeper finished.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Keep PC active and Teams green without mouse clicks")
    parser.add_argument('--config', type=str, default='activity_config.json', help='Configuration file')
    parser.add_argument('--interval', type=int, help='Activity interval in seconds')
    parser.add_argument('--duration', type=int, help='Total duration in seconds')
    parser.add_argument('--method', choices=['keyboard', 'mouse'], help='Activity method')
    args = parser.parse_args()

    config = load_config(args.config)

    # Check if within scheduled hours
    if not is_within_schedule(config):
        print("Outside scheduled hours. Exiting.")
        print(f"Schedule: {config.get('work_hours_start')} - {config.get('work_hours_end')}")
        print(f"Work days: {config.get('work_days')}")
        sys.exit(0)

    # Override config with command line args if provided
    activity_interval = args.interval or config.get('activity_interval', 120)
    total_duration = args.duration or config.get('total_duration', 18000)
    method = args.method or config.get('method', 'mouse')
    keyboard_key = config.get('keyboard_key', 'scrolllock')
    mouse_distance = config.get('mouse_move_distance', 10)

    # Handle keyboard interrupt
    def signal_handler(sig: int, frame: object) -> None:
        logger.info("Script interrupted by user")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    keep_active(activity_interval, total_duration, method, keyboard_key, mouse_distance, config)


if __name__ == "__main__":
    main()
