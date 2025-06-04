"""Account management for gitswitch."""

import logging
from typing import Dict, List, Optional, Tuple

from .config import ConfigManager
from .exceptions import AccountNotFoundError
from .utils import normalize_account_key

logger = logging.getLogger(__name__)


class AccountManager:
    """Account manager focused on data access."""

    def __init__(self, config_manager: ConfigManager = None):
        self.config_manager = config_manager or ConfigManager()
        self._accounts_cache = None

    def _clear_cache(self):
        """Clear the accounts cache."""
        self._accounts_cache = None

    def get_accounts(self, force_reload: bool = False) -> Tuple[bool, Dict[int, dict], str]:
        """Get all accounts with caching. Returns (success, accounts_dict, message)."""
        if self._accounts_cache is None or force_reload:
            success, config, message = self.config_manager.load_config()
            if not success:
                return False, {}, f"Failed to load configuration: {message}"
            
            accounts_data = config.get("accounts", {})

            # Convert string keys to integers
            self._accounts_cache = {}
            invalid_keys = []
            
            for key, account in accounts_data.items():
                try:
                    account_num = normalize_account_key(key)
                    self._accounts_cache[account_num] = account
                except ValueError as e:
                    logger.warning(f"Skipping invalid account key: {e}")
                    invalid_keys.append(str(key))

            if invalid_keys:
                warning_msg = f"Loaded {len(self._accounts_cache)} accounts (skipped invalid keys: {', '.join(invalid_keys)})"
            else:
                warning_msg = f"Loaded {len(self._accounts_cache)} accounts successfully"
        else:
            # Cache hit - return cached data
            warning_msg = f"Using cached accounts ({len(self._accounts_cache)} accounts)"

        return True, self._accounts_cache.copy(), warning_msg

    def get_account(self, identifier, accounts: Dict[int, dict] = None) -> Tuple[bool, int, dict, str]:
        """Get account by number or search term. Returns (success, account_num, account_data, message)."""
        if accounts is None:
            success, accounts, message = self.get_accounts()
            if not success:
                return False, -1, {}, f"Failed to load accounts: {message}"

        # Try numeric lookup first
        try:
            account_num = int(identifier)
            if account_num in accounts:
                return True, account_num, accounts[account_num], f"Found account #{account_num}"
        except (ValueError, TypeError):
            pass

        # Search by text using new tuple-returning method
        search_success, matches, search_message = self.search_accounts(identifier, accounts)
        if not search_success:
            return False, -1, {}, f"Search failed: {search_message}"

        if len(matches) == 0:
            return False, -1, {}, f"No accounts found matching '{identifier}'"
        elif len(matches) == 1:
            account_num, account_data = matches[0]
            return True, account_num, account_data, f"Found account #{account_num} matching '{identifier}'"
        else:
            # Multiple matches
            match_details = [f"#{num}: {acc['description']}" for num, acc in matches]
            return False, -1, {}, f"Multiple accounts found matching '{identifier}': {', '.join(match_details)}"

    def search_accounts(self, query: str, accounts: Dict[int, dict] = None) -> Tuple[bool, List[Tuple[int, dict]], str]:
        """Search for accounts by description, name, or email. Returns (success, matches, message)."""
        if accounts is None:
            success, accounts, message = self.get_accounts()
            if not success:
                return False, [], f"Failed to load accounts: {message}"

        if not query:
            return True, [], "Empty query provided"

        query = query.lower().strip()
        matches = []

        for account_num, account in accounts.items():
            searchable_fields = [
                account.get("description", ""),
                account.get("name", ""),
                account.get("email", ""),
            ]

            if any(query in field.lower() for field in searchable_fields):
                matches.append((account_num, account))

        return True, matches, f"Found {len(matches)} matching accounts"

    def add_account(self, account_data: dict) -> Tuple[bool, int, str]:
        """Add a new account. Returns (success, account_num, message)."""
        try:
            # Get next account number
            success, accounts, load_message = self.get_accounts()
            if not success:
                return False, -1, f"Failed to load existing accounts: {load_message}"
            
            account_num = max(accounts.keys()) + 1 if accounts else 1

            # Load config and add account
            success, config, config_message = self.config_manager.load_config()
            if not success:
                return False, -1, f"Failed to load configuration: {config_message}"
            
            if "accounts" not in config:
                config["accounts"] = {}

            config["accounts"][str(account_num)] = account_data

            # Save config
            success, save_message = self.config_manager.save_config(config)
            if not success:
                return False, -1, f"Failed to save configuration: {save_message}"
            
            self._clear_cache()

            logger.info(f"Added account #{account_num}: {account_data.get('description')}")
            return True, account_num, f"Successfully added account #{account_num}: {account_data.get('description', 'No description')}"

        except Exception as e:
            logger.error(f"Unexpected error adding account: {e}")
            return False, -1, f"Unexpected error adding account: {e}"

    def update_account(self, account_num: int, account_data: dict) -> Tuple[bool, str]:
        """Update an existing account. Returns (success, message)."""
        try:
            # Check if account exists
            success, accounts, load_message = self.get_accounts()
            if not success:
                return False, f"Failed to load accounts: {load_message}"
            
            if account_num not in accounts:
                return False, f"Account #{account_num} not found"

            # Load config and update account
            success, config, config_message = self.config_manager.load_config()
            if not success:
                return False, f"Failed to load configuration: {config_message}"
            
            config["accounts"][str(account_num)] = account_data

            # Save config
            success, save_message = self.config_manager.save_config(config)
            if not success:
                return False, f"Failed to save configuration: {save_message}"
            
            self._clear_cache()

            logger.info(f"Updated account #{account_num}: {account_data.get('description')}")
            return True, f"Successfully updated account #{account_num}: {account_data.get('description', 'No description')}"

        except Exception as e:
            logger.error(f"Unexpected error updating account: {e}")
            return False, f"Unexpected error updating account: {e}"

    def remove_account(self, account_num: int) -> Tuple[bool, str]:
        """Remove an account. Returns (success, message)."""
        try:
            # Check if account exists
            success, accounts, load_message = self.get_accounts()
            if not success:
                return False, f"Failed to load accounts: {load_message}"
            
            if account_num not in accounts:
                return False, f"Account #{account_num} not found"

            account_description = accounts[account_num].get('description', f'Account #{account_num}')

            # Load config and remove account
            success, config, config_message = self.config_manager.load_config()
            if not success:
                return False, f"Failed to load configuration: {config_message}"
            
            if str(account_num) in config.get("accounts", {}):
                del config["accounts"][str(account_num)]
                
                success, save_message = self.config_manager.save_config(config)
                if not success:
                    return False, f"Failed to save configuration: {save_message}"
                
                self._clear_cache()
                logger.info(f"Removed account #{account_num}")
                return True, f"Successfully removed account #{account_num}: {account_description}"

            return False, f"Account #{account_num} not found in configuration"

        except Exception as e:
            logger.error(f"Unexpected error removing account: {e}")
            return False, f"Unexpected error removing account: {e}"

    def get_account_preferred_scope(self, account: dict) -> Tuple[bool, str, str]:
        """Get the preferred scope for a specific account. Returns (success, scope, message)."""
        try:
            account_scope = account.get("preferred_scope")
            if account_scope:
                return True, account_scope, f"Using account preferred scope: {account_scope}"
            
            # Fall back to default scope from config
            success, default_scope, scope_message = self.config_manager.get_default_scope()
            if not success:
                return False, "local", f"Could not get default scope, using 'local': {scope_message}"
            
            return True, default_scope, f"Using default scope: {default_scope}"
            
        except Exception as e:
            logger.error(f"Error getting preferred scope: {e}")
            return False, "local", f"Error getting preferred scope, using 'local': {e}"

    # Legacy methods for backward compatibility (these raise exceptions as before)
    # These can be removed once all calling code is updated

    def get_accounts_legacy(self, force_reload: bool = False) -> Dict[int, dict]:
        """Legacy method - raises exceptions. Use get_accounts() instead."""
        success, accounts, message = self.get_accounts(force_reload)
        if not success:
            raise Exception(message)
        return accounts

    def get_account_legacy(self, identifier, accounts: Dict[int, dict] = None) -> Tuple[int, dict]:
        """Legacy method - raises exceptions. Use get_account() instead."""
        success, account_num, account_data, message = self.get_account(identifier, accounts)
        if not success:
            raise AccountNotFoundError(message)
        return account_num, account_data

    def add_account_legacy(self, account_data: dict) -> int:
        """Legacy method - raises exceptions. Use add_account() instead."""
        success, account_num, message = self.add_account(account_data)
        if not success:
            raise Exception(message)
        return account_num

    def update_account_legacy(self, account_num: int, account_data: dict) -> bool:
        """Legacy method - raises exceptions. Use update_account() instead."""
        success, message = self.update_account(account_num, account_data)
        if not success:
            raise Exception(message)
        return True

    def remove_account_legacy(self, account_num: int) -> bool:
        """Legacy method - raises exceptions. Use remove_account() instead."""
        success, message = self.remove_account(account_num)
        if not success:
            raise Exception(message)
        return True

    def get_account_preferred_scope_legacy(self, account: dict) -> str:
        """Legacy method - raises exceptions. Use get_account_preferred_scope() instead."""
        success, scope, message = self.get_account_preferred_scope(account)
        if not success:
            raise Exception(message)
        return scope