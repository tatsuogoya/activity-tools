import pyautogui as pag
import time
import random
import argparse
import json
import os
import signal
import sys

# Enable pyautogui failsafe
pag.FAILSAFE = True

def randomize_position(x, y, jitter=3):
    """Slightly randomize x and y coordinates to simulate human movement."""
    return x + random.randint(-jitter, jitter), y + random.randint(-jitter, jitter)

def randomize_duration(base_duration, variation=0.5):
    """Randomize duration to simulate human timing."""
    return base_duration * random.uniform(1 - variation, 1 + variation)

def log(message, log_file=None):
    """Prints a timestamped message and optionally writes to file."""
    timestamp = time.strftime("%Y-%m-%d %I:%M:%S %p", time.localtime())
    formatted_message = f"[{timestamp}] {message}"
    print(formatted_message)
    if log_file:
        with open(log_file, 'a') as f:
            f.write(formatted_message + '\n')

def load_config(config_file='config.json'):
    """Load configuration from JSON file."""
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    else:
        # Default config
        return {
            "total_moves": 10,
            "move_duration": 2.0,
            "sleep_between_clicks": 5.0,
            "long_sleep_duration": 100.0,
            "left_click_coords": [1450, 80],
            "right_click_coords": [1450, 950],
            "jitter_range": 3,
            "duration_variation": 0.5
        }

def save_config(config, config_file='config.json'):
    """Save configuration to JSON file."""
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)

def perform_click(x, y, click_type='left', duration=2.0, jitter=3, duration_variation=0.5, dry_run=False):
    """Perform a mouse click with randomization."""
    rx, ry = randomize_position(x, y, jitter)
    rd = randomize_duration(duration, duration_variation)
    if not dry_run:
        pag.moveTo(rx, ry, duration=rd)
        if click_type == 'left':
            pag.click()
        elif click_type == 'right':
            pag.rightClick()
    else:
        time.sleep(rd)  # Simulate the duration
    return rx, ry

def main():
    parser = argparse.ArgumentParser(description="Mouse automation script")
    parser.add_argument('--config', type=str, default='config.json', help='Configuration file')
    parser.add_argument('--log', type=str, help='Log file')
    parser.add_argument('--dry-run', action='store_true', help='Simulate actions without moving the mouse')
    args = parser.parse_args()

    config = load_config(args.config)

    log_file = args.log
    dry_run = args.dry_run

    if dry_run:
        log("DRY RUN MODE: Simulating actions without actual mouse movement", log_file)

    log(f"Script started. Total planned moves: {config['total_moves']}", log_file)

    # Handle keyboard interrupt
    def signal_handler(sig, frame):
        log("Script interrupted by user", log_file)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    counter = 0

    try:
        for counter in range(config['total_moves']):
            # Left click action
            x1, y1 = perform_click(
                *config['left_click_coords'],
                'left',
                config['move_duration'],
                config['jitter_range'],
                config['duration_variation'],
                dry_run
            )
            log(f"Move {counter + 1}: Left clicked at ({x1}, {y1})", log_file)
            time.sleep(config['long_sleep_duration'])

            # Right click action
            x2, y2 = perform_click(
                *config['right_click_coords'],
                'right',
                config['move_duration'],
                config['jitter_range'],
                config['duration_variation'],
                dry_run
            )
            log(f"Move {counter + 1}: Right clicked at ({x2}, {y2})", log_file)

            time.sleep(config['sleep_between_clicks'])

    except pag.FailSafeException:
        log("Failsafe triggered: Mouse moved to corner", log_file)
    except Exception as e:
        log(f"An error occurred: {e}", log_file)

    finally:
        log(f"Script finished. Total moves completed: {counter + 1}", log_file)

if __name__ == "__main__":
    main()