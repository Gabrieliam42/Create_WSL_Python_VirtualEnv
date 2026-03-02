# Script Developer: Gabriel Mihai Sandu
# GitHub Profile: https://github.com/Gabrieliam42

import os
import sys
import ctypes
import tkinter as tk
from tkinter import filedialog
import subprocess
import shlex

DISTRO_NAME = "Ubuntu"

def get_current_directory():
    return os.getcwd()

def check_admin_privileges():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def run_as_admin(script, params):
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)

def pause_and_exit(message, code=1):
    print(message)
    try:
        input("Press Enter to exit...")
    except EOFError:
        pass
    sys.exit(code)

def ensure_wsl_available():
    try:
        subprocess.run(
            ["wsl", "-d", DISTRO_NAME, "-e", "bash", "-lc", "exit 0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        pause_and_exit("WSL command not found. Ensure WSL is installed and available in PATH.")
    except subprocess.CalledProcessError as exc:
        error_text = (exc.stderr or "").strip()
        if error_text:
            pause_and_exit(
                f"Unable to run 'wsl -d {DISTRO_NAME}'. Ensure the distro exists and WSL is working.\n{error_text}"
            )
        pause_and_exit(f"Unable to run 'wsl -d {DISTRO_NAME}'. Ensure the distro exists and WSL is working.")

def convert_windows_path_to_wsl(path):
    result = subprocess.run(
        ["wsl", "-d", DISTRO_NAME, "-e", "wslpath", "-a", "-u", path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        error_text = result.stderr.strip() or "Unknown error while converting Windows path to WSL path."
        pause_and_exit(f"Failed to convert Windows path to WSL path: {error_text}")

    converted_path = result.stdout.strip()
    if not converted_path:
        pause_and_exit("Failed to convert Windows path to WSL path: empty result.")
    return converted_path

def find_activate_paths_in_wsl_cwd(wsl_cwd):
    bash_script = f"""
set -e
cd -- {shlex.quote(wsl_cwd)}
find . -type f -path "*/bin/activate" | sort
"""
    result = subprocess.run(
        ["wsl", "-d", DISTRO_NAME, "-e", "bash", "-lc", bash_script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        error_text = result.stderr.strip() or "Unknown error while scanning for virtual environments."
        pause_and_exit(f"Failed to search for virtual environments in WSL: {error_text}")

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]

def select_activate_path(activate_paths):
    if len(activate_paths) == 1:
        return activate_paths[0]

    print("Virtual environments found in the current directory tree:")
    for index, activate_path in enumerate(activate_paths, start=1):
        print(f"{index}. {activate_path}")

    while True:
        user_choice = input("Select the number of the virtual environment you want to activate: ").strip()
        if user_choice.isdigit():
            choice = int(user_choice)
            if 1 <= choice <= len(activate_paths):
                return activate_paths[choice - 1]
        print(f"Invalid selection. Enter a number between 1 and {len(activate_paths)}.")

def select_python_file(initial_dir):
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[("Python files", "*.py")])
    root.destroy()
    return file_path

def find_python_files(cwd):
    py_files = []
    for root, dirs, files in os.walk(cwd):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    return py_files

def run_python_file_with_venv(file_path, wsl_cwd, activate_path):
    wsl_script_path = convert_windows_path_to_wsl(file_path)
    bash_script = (
        f"set -e; "
        f"cd -- {shlex.quote(wsl_cwd)}; "
        f"source {shlex.quote(activate_path)}; "
        f'echo "Activated virtual environment from: {activate_path}"; '
        f"python3 {shlex.quote(wsl_script_path)}"
    )
    subprocess.run(["wsl", "-d", DISTRO_NAME, "-e", "bash", "-lc", bash_script])

def main():
    cwd = get_current_directory()
    print(f"Current working directory: {cwd}")

    if not check_admin_privileges():
        print("Script is not running with admin privileges. Restarting with admin privileges...")
        run_as_admin(__file__, "")
        return

    ensure_wsl_available()
    wsl_cwd = convert_windows_path_to_wsl(cwd)

    activate_paths = find_activate_paths_in_wsl_cwd(wsl_cwd)
    if not activate_paths:
        pause_and_exit(
            "No virtual environment activation script found in the current directory or its subdirectories."
        )

    selected_activate = select_activate_path(activate_paths)

    py_files = find_python_files(cwd)
    if not py_files:
        print("No .py files found in the current directory or its subdirectories.")
        return

    selected_file = select_python_file(cwd)
    if not selected_file:
        print("No file selected.")
        return

    run_python_file_with_venv(selected_file, wsl_cwd, selected_activate)

if __name__ == "__main__":
    main()
