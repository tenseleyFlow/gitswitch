"""Git command operations for gitswitch."""

import subprocess
import re


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


def run_git_command_silent(command):
    """Run a git command silently (don't print errors)"""
    try:
        result = subprocess.run(command, shell=True,
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # Silently return None if command fails (e.g., config doesn't exist)
        return None


def validate_gpg_key(key_id):
    """Validate that a GPG key exists and is usable"""
    if not key_id:
        return False, "No key ID provided"

    try:
        # Check if key exists in secret keyring
        result = subprocess.run(
            f"gpg --list-secret-keys --keyid-format=long {key_id}",
            shell=True, capture_output=True, text=True, check=True
        )

        if key_id in result.stdout:
            return True, "GPG key is valid"
        else:
            return False, f"GPG key {key_id} not found in secret keyring"

    except subprocess.CalledProcessError:
        return False, f"GPG key {key_id} not found or invalid"


def clear_local_git_config():
    """Clear local git configuration to allow global settings to take effect"""
    configs_to_clear = [
        "user.name",
        "user.email", 
        "user.signingkey",
        "commit.gpgsign",
        "tag.gpgsign"
    ]

    cleared = []
    for config in configs_to_clear:
        # Check if local config exists (SILENTLY)
        result = run_git_command_silent(f"git config --local {config}")
        if result:  # Config exists locally
            # Unset it
            unset_result = run_git_command_silent(f"git config --local --unset {config}")
            if unset_result is not None:  # Successful unset (or at least didn't fail)
                cleared.append(config)

    return cleared


def get_current_config(scope=None):
    """Get current git user configuration"""
    scope_flag = ""
    if scope == "global":
        scope_flag = " --global"
    elif scope == "local":
        scope_flag = " --local"

    name = run_git_command_silent(f"git config{scope_flag} user.name")
    email = run_git_command_silent(f"git config{scope_flag} user.email")
    return name, email


def get_gpg_config(scope=None):
    """Get current GPG configuration"""
    scope_flag = ""
    if scope == "global":
        scope_flag = " --global"
    elif scope == "local":
        scope_flag = " --local"

    signing_key = run_git_command_silent(f"git config{scope_flag} user.signingkey")
    commit_sign = run_git_command_silent(f"git config{scope_flag} commit.gpgsign")
    tag_sign = run_git_command_silent(f"git config{scope_flag} tag.gpgsign")

    return {
        "signing_key": signing_key,
        "commit_gpgsign": commit_sign == "true",
        "tag_gpgsign": tag_sign == "true"
    }


def set_git_config(account_info, scope="local"):
    """Set git user configuration with specified scope"""
    scope_flag = f"--{scope}" if scope in ["global", "local"] else ""

    # If setting global scope, clear local configs first
    if scope == "global":
        cleared_configs = clear_local_git_config()
        if cleared_configs:
            print(f"🧹 Cleared local git config: {', '.join(cleared_configs)}")
            print("   (This allows global settings to take effect)")

    name_cmd = f'git config {scope_flag} user.name "{account_info["name"]}"'.strip()
    email_cmd = f'git config {scope_flag} user.email "{account_info["email"]}"'.strip()

    success = True

    # Set basic user config
    name_result = run_git_command_silent(name_cmd)
    email_result = run_git_command_silent(email_cmd)

    if name_result is None or email_result is None:
        print("❌ Failed to set basic git configuration")
        return False

    # Handle GPG configuration
    gpg_key = account_info.get("gpg_key")
    signing_enabled = account_info.get("signing_enabled", False)

    if gpg_key and signing_enabled:
        # Validate GPG key exists
        is_valid, message = validate_gpg_key(gpg_key)
        if not is_valid:
            print(f"⚠️  GPG Warning: {message}")
            print("   Proceeding without GPG signing...")
            success = set_gpg_config_disabled(scope_flag)
        else:
            success = set_gpg_config_enabled(gpg_key, scope_flag)
    else:
        # Disable or don't set GPG signing
        success = set_gpg_config_disabled(scope_flag)

    if success:
        scope_text = f" ({scope})" if scope else ""
        print(f"✅ Successfully switched to: {account_info['description']}{scope_text}")
        print(f"   Name: {account_info['name']}")
        print(f"   Email: {account_info['email']}")
        print(f"   Scope: {scope}")

        # Show GPG status
        if gpg_key and signing_enabled:
            print(f"   GPG Key: {gpg_key}")
            print(f"   GPG Signing: {'✅ Enabled' if signing_enabled else '❌ Disabled'}")
        else:
            print("   GPG Signing: ❌ Disabled")

        return True
    else:
        print("❌ Failed to set git configuration")
        return False


def set_gpg_config_enabled(gpg_key, scope_flag):
    """Enable GPG signing with specified key"""
    key_cmd = f'git config {scope_flag} user.signingkey "{gpg_key}"'.strip()
    commit_sign_cmd = f'git config {scope_flag} commit.gpgsign true'.strip()
    tag_sign_cmd = f'git config {scope_flag} tag.gpgsign true'.strip()

    key_result = run_git_command_silent(key_cmd)
    commit_result = run_git_command_silent(commit_sign_cmd)
    tag_result = run_git_command_silent(tag_sign_cmd)

    return (key_result is not None and
            commit_result is not None and
            tag_result is not None)


def set_gpg_config_disabled(scope_flag):
    """Disable GPG signing"""
    commit_sign_cmd = f'git config {scope_flag} commit.gpgsign false'.strip()
    tag_sign_cmd = f'git config {scope_flag} tag.gpgsign false'.strip()

    commit_result = run_git_command_silent(commit_sign_cmd)
    tag_result = run_git_command_silent(tag_sign_cmd)

    return (commit_result is not None and tag_result is not None)


def get_git_scope_info():
    """Get information about current git configuration scope"""
    global_name, global_email = get_current_config("global")
    local_name, local_email = get_current_config("local")
    global_gpg = get_gpg_config("global")
    local_gpg = get_gpg_config("local")

    return {
        "global": {
            "name": global_name,
            "email": global_email,
            "gpg": global_gpg
        },
        "local": {
            "name": local_name,
            "email": local_email,
            "gpg": local_gpg
        }
    }
