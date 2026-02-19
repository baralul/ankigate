import sys
import time
import requests
import subprocess
import json
import os
import textwrap
import winsound

# --- 1. CONFIGURATION ---
# These variables define PATHS. Python does not open the files yet.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
REDIRECT = "127.0.0.1"

# --- 2. UTILITY FUNCTIONS ---
def load_config():
    """Reads the JSON config. Only fails if file is literally missing."""
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def flush_dns():
    """Cleans the DNS cache and resets the resolver cache."""
    # Standard flush
    subprocess.run(["ipconfig", "/flushdns"], capture_output=True, shell=True)
    # Register DNS forces the OS to re-read the hosts file immediately
    subprocess.run(["ipconfig", "/registerdns"], capture_output=True, shell=True)
    print("DNS Flushed and Registered. Access updated.")

def get_review_count(url):
    """Pings AnkiConnect to get the number of reviewed cards."""
    try:
        r = requests.post(url, json={'action': 'findCards', 'params': {'query': 'rated:1'}, 'version': 6})
        return len(r.json()['result'])
    except:
        return None

def display_progress(current, start, quota):
    """Updates the progress in the same line of the terminal."""
    done = current - start
    sys.stdout.write(f"\rProgress: {done}/{quota} cards completed")
    sys.stdout.flush()

def ensure_config_exists():
    """CRITICAL: Creates the file if it doesn't exist so load_config() won't crash."""
    if not os.path.exists(CONFIG_PATH):
        default_config = {
            "ANKI_URL": "http://localhost:8765",
            "WEBSITES": ["www.youtube.com", "youtube.com", "www.reddit.com", "reddit.com"],
            "CARD_TO_MINUTE_RATIO": 5,
            "DEFAULT_REWARD_IN_MINUTE": 1
        }
        with open(CONFIG_PATH, 'w') as f:
            json.dump(default_config, f, indent=4)
        
        print(f"--- FIRST RUN DETECTED ---")
        print(f"Created a default config.json at: {CONFIG_PATH}")
        print(f"Please edit this file to add your specific blocked websites.")
        print(f"---------------------------\n")

# --- 3. LOGIC FUNCTIONS ---
def block_sites(websites):
    """Writes redirect lines to the hosts file."""
    with open(HOSTS_PATH, 'r+') as file:
        content = file.read()
        for site in websites:
            if site not in content:
                file.write(f"{REDIRECT} {site}\n")
    print("\n--- SITES BLOCKED ---")

def unblock_sites(websites, manual=False):
    """Removes the redirect lines from the hosts file."""
    with open(HOSTS_PATH, 'r') as file:
        lines = file.readlines()
    with open(HOSTS_PATH, 'w') as file:
        for line in lines:
            if not any(site in line for site in websites):
                file.write(line)
    
    # Play success sound only for earned rewards
    if not manual:
        sound_path = os.path.join(SCRIPT_DIR, "success.wav")
        if os.path.exists(sound_path):
            winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
    
    print("\n--- SITES UNBLOCKED ---")

def handle_arguments(config):
    """Parses CLI args and returns (minutes, should_exit)"""
    
    # Notice the leading \n to create that specific Windows CLI head-space
    help_menu = textwrap.dedent(f"""
        Usage: ankigate [-d] [-<minutes>] [-u]

        Options:
            -d             Start session with default ({config['DEFAULT_REWARD_IN_MINUTE']}m).
            -<minutes>     Start session with custom reward minutes.
            -u             Emergency unblock: Cleans the hosts file and exits.
    """).strip()

    # 1. No arguments: Prints a blank line THEN the usage
    if len(sys.argv) == 1:
        print(f"\n{help_menu}")
        return None, True

    arg = sys.argv[1]

    # 2. Valid Commands
    if arg == "-u":
        unblock_sites(config["WEBSITES"], manual=True)
        flush_dns()
        return None, True

    if arg == "-d":
        return config["DEFAULT_REWARD_IN_MINUTE"], False

    # 3. Numeric Override (e.g., -5)
    if arg.startswith('-') and len(arg) > 1:
        try:
            return int(arg[1:]), False
        except ValueError:
            pass

    # 4. Invalid Command: Prints error, blank line, then usage
    print(f"{arg} is not a valid command option.\n")
    print(help_menu)
    return None, True

# --- 4. THE MAIN CONTROLLER ---
def main():
    # 1. First, make sure the file exists
    ensure_config_exists()
    
    # 2. Now it is safe to read it
    config = load_config()
    
    # 3. Handle Arguments
    minutes, should_exit = handle_arguments(config)
    if should_exit:
        return

    # 4. Set up session
    quota = minutes * config["CARD_TO_MINUTE_RATIO"]
    reward_seconds = minutes * 60

    print(f"--- ANKIGATE STARTED ---")
    print(f"Goal: {quota} cards | Reward: {minutes} minutes")

    block_sites(config["WEBSITES"])
    flush_dns()
    
    last_count = get_review_count(config["ANKI_URL"])
    if last_count is None:
        print("Error: Could not connect to Anki. Is Anki open and AnkiConnect installed?")
        return

    # 5. Monitoring Loop
    try:
        while True:
            current_count = get_review_count(config["ANKI_URL"])
            if current_count is not None:
                display_progress(current_count, last_count, quota)
                
                if current_count >= last_count + quota:
                    unblock_sites(config["WEBSITES"])
                    time.sleep(reward_seconds)
                    block_sites(config["WEBSITES"])
                    flush_dns()
                    last_count = get_review_count(config["ANKI_URL"])
            else:
            # If we get None (When anki is likely syncing or closed it may become unresponsive)
                pass
            time.sleep(1.5)
    except KeyboardInterrupt:
        print("\n\nAnkigate closed. Sites remain blocked for focus!")

if __name__ == "__main__":
    main()