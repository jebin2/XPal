
import subprocess
import os

def save_active_window():
	"""Save the currently active window handle for later restoration"""
	if os.getenv("neko_url", "") == "":
		script_dir = os.path.dirname(os.path.abspath(__file__))
		ps_script = os.path.join(script_dir, "window_control.ps1")
		subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", ps_script, "-action", "save"])

def minimize_active_window():
	"""Function to minimize the currently active window"""
	if os.getenv("neko_url", "") == "":
		script_dir = os.path.dirname(os.path.abspath(__file__))
		ps_script = os.path.join(script_dir, "window_control.ps1")
		subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", ps_script, "-action", "minimize"])

def restore_previous_focus():
	"""Function to restore focus to the previously saved window with click"""
	if os.getenv("neko_url", "") == "":
		script_dir = os.path.dirname(os.path.abspath(__file__))
		ps_script = os.path.join(script_dir, "window_control.ps1")
		subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", ps_script, "-action", "restoreFocus"])
