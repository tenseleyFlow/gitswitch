"""Git command operations for gitswitch."""

import subprocess


def run_git_command(command, scope=None):
    """Run a git command and return the result"""
    # Add scope flag if specified
    if scope == "global":
        command = command.replace("git config", "git config --global")
    elif scope == "local":
        command = command.replace("git config", "git config --local")
    # If scope is None, use git's default behavior

    try:
        result = subprocess.run(command, shell=True,
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None


def get_current_config(scope=None):
    """Get current git user configuration"""
    scope_flag = ""
    if scope == "global":
        scope_flag = " --global"
    elif scope == "local":
        scope_flag = " --local"

    name = run_git_command(f"git config{scope_flag} user.name")
    email = run_git_command(f"git config{scope_flag} user.email")
    return name, email


def set_git_config(account_info, scope="local"):
    """Set git user configuration with specified scope"""
    scope_flag = f"--{scope}" if scope in ["global", "local"] else ""

    name_cmd = f'git config {scope_flag} user.name "{account_info["name"]}"'.strip()
    email_cmd = f'git config {scope_flag} user.email "{account_info["email"]}"'.strip()

    if (run_git_command(name_cmd) is not None
        and run_git_command(email_cmd) is not None):
        scope_text = f" ({scope})" if scope else ""
        print(f"✅ Successfully switched to: {account_info['description']}{scope_text}")
        print(f"   Name: {account_info['name']}")
        print(f"   Email: {account_info['email']}")
        print(f"   Scope: {scope}")
        return True
    else:
        print("❌ Failed to set git configuration")
        return False


def get_git_scope_info():
    """Get information about current git configuration scope"""
    global_name, global_email = get_current_config("global")
    local_name, local_email = get_current_config("local")

    return {
        "global": {"name": global_name, "email": global_email},
        "local": {"name": local_name, "email": local_email}
    }
