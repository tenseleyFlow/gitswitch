# gitswitch
(noun) : something clever someday

### what is this?
This is a little tool I use to manage and switch between git configs quicker as I somehow have 3 GH accounts.
Reads account details from a toml file in $HOME/.config/gitswitch/accounts.toml

Installation:
~~clone this repo and `cd` into it. From there run: `pip install -e .` and `gitswitch` is available in that environment[^1].~~  
Just use the makefile:
```
  make install      - pip install -e . && asdf reshim python
  make uninstall    - pip uninstall gitswitch
  make clean        - rm -rf **/*/*.egg-info
  make reshim       - asdf reshim python
  make reinstall    - Uninstall, clean, then install & reshim
```

Example usage:
```
  gitswitch                    # Interactive account switching
  gitswitch 2                  # Switch directly to account #2
  gitswitch work               # Switch to account matching "work"
  gitswitch add                # Add a new account
  gitswitch edit 2             # Edit account #2
  gitswitch remove             # Remove an account
  gitswitch list               # List all accounts
  gitswitch status             # Show current git configuration scope
  gitswitch config             # Edit config file in $EDITOR
  gitswitch doctor             # Run comprehensive health check
  gitswitch validate           # Validate configuration and accounts
```

[^1]: if you use a version manager like `asdf`, you may need to reshim to make the command available.
