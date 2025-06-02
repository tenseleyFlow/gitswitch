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

    def get_accounts(self, force_reload: bool = False) -> Dict[int, dict]:
        """Get all accounts with caching."""
        if self._accounts_cache is None or force_reload:
            config = self.config_manager.load_config()
            accounts_data = config.get("accounts", {})

            # Convert string keys to integers
            self._accounts_cache = {}
            for key, account in accounts_data.items():
                try:
                    account_num = normalize_account_key(key)
                    self._accounts_cache[account_num] = account
                except ValueError as e:
                    logger.warning(f"Skipping invalid account key: {e}")

        return self._accounts_cache.copy()

    def get_account(self, identifier, accounts: Dict[int, dict] = None) -> Tuple[int, dict]:
        """Get account by number or search term from provided accounts dict or load if needed."""
        if accounts is None:
            accounts = self.get_accounts()

        # Try numeric lookup first
        try:
            account_num = int(identifier)
            if account_num in accounts:
                return account_num, accounts[account_num]
        except (ValueError, TypeError):
            pass

        # Search by text
        matches = self.search_accounts(identifier, accounts)

        if len(matches) == 0:
            raise AccountNotFoundError(f"No accounts found matching '{identifier}'")
        elif len(matches) == 1:
            return matches[0]
        else:
            # Multiple matches
            match_details = [f"#{num}: {acc['description']}" for num, acc in matches]
            raise AccountNotFoundError(f"Multiple accounts found matching '{identifier}': {', '.join(match_details)}")

    def search_accounts(self, query: str, accounts: Dict[int, dict] = None) -> List[Tuple[int, dict]]:
        """Search for accounts by description, name, or email."""
        if accounts is None:
            accounts = self.get_accounts()

        if not query:
            return []

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

        return matches

    def add_account(self, account_data: dict) -> int:
        """Add a new account."""
        # Get next account number
        accounts = self.get_accounts()
        account_num = max(accounts.keys()) + 1 if accounts else 1

        # Load config and add account
        config = self.config_manager.load_config()
        if "accounts" not in config:
            config["accounts"] = {}

        config["accounts"][str(account_num)] = account_data

        # Save config
        self.config_manager.save_config(config)
        self._clear_cache()

        logger.info(f"Added account #{account_num}: {account_data.get('description')}")
        return account_num

    def update_account(self, account_num: int, account_data: dict) -> bool:
        """Update an existing account."""
        # Check if account exists
        accounts = self.get_accounts()
        if account_num not in accounts:
            raise AccountNotFoundError(f"Account #{account_num} not found")

        # Load config and update account
        config = self.config_manager.load_config()
        config["accounts"][str(account_num)] = account_data

        # Save config
        self.config_manager.save_config(config)
        self._clear_cache()

        logger.info(f"Updated account #{account_num}: {account_data.get('description')}")
        return True

    def remove_account(self, account_num: int) -> bool:
        """Remove an account."""
        # Check if account exists
        accounts = self.get_accounts()
        if account_num not in accounts:
            raise AccountNotFoundError(f"Account #{account_num} not found")

        # Load config and remove account
        config = self.config_manager.load_config()
        if str(account_num) in config.get("accounts", {}):
            del config["accounts"][str(account_num)]
            self.config_manager.save_config(config)
            self._clear_cache()
            logger.info(f"Removed account #{account_num}")
            return True

        return False

    def get_account_preferred_scope(self, account: dict) -> str:
        """Get the preferred scope for a specific account."""
        return account.get("preferred_scope", self.config_manager.get_default_scope())
