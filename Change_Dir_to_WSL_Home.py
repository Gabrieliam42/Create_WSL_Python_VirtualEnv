# Script Developer: Gabriel Mihai Sandu
# GitHub Profile: https://github.com/Gabrieliam42

import os
import sys
import subprocess

def is_wsl():
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except FileNotFoundError:
        return False

def change_dir_to_WSL():
    # Use the Linux native home directory
    home_dir = os.path.expanduser("~")
    
    try:
        # Change the current working directory to the Linux native home directory
        os.chdir(home_dir)
        print(f"Changed current directory to {home_dir}")
        
        # Open an interactive shell so the terminal stays open
        shell = os.environ.get("SHELL", "/bin/bash")
        subprocess.run([shell])
        
    except Exception as e:
        print(f"Error while changing directory: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if not is_wsl():
        print("This script must be run inside WSL2. Exiting...")
        sys.exit(1)
    
    change_dir_to_WSL()
