"""Git command operations for gitswitch."""

import subprocess


def run_git_command(command):
    """Run a git command and return the result"""
    try:
        result = subprocess.run(command, shell=True,
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None


def get_current_config():
    """Get current git user configuration"""
    name = run_git_command("git config user.name")
    email = run_git_command("git config user.email")
    return name, email


def set_git_config(account_info):
    """Set git user configuration"""
    name_cmd = f'git config user.name "{account_info["name"]}"'
    email_cmd = f'git config user.email "{account_info["email"]}"'

    if (run_git_command(name_cmd) is not None
        and run_git_command(email_cmd) is not None):
        print(f"✅ Successfully switched to: {account_info['description']}")
        print(f"   Name: {account_info['name']}")
        print(f"   Email: {account_info['email']}")
        return True
    else:
        print("❌ Failed to set git configuration")
        return False
