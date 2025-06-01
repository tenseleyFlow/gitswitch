# gitswitch
(noun) : something clever someday

### what is this?
This is a little tool I use to manage and switch between git configs quicker as I somehow have 3 GH accounts.
Reads account details from a toml file in $HOME/.config/gitswitch/accounts.toml

Installation:
clone this repo and `cd` into it. From there run: `pip install -e .` and `gitswitch` is available in that environment[^1].  

Usage:
```
  gitswitch                    # Interactive account switching
  gitswitch 2                  # Switch directly to account #2
  gitswitch add                # Add a new account
  gitswitch remove             # Remove an account
  gitswitch list               # List all accounts
  gitswitch status             # Show current git configuration scope
  gitswitch --global 1         # Switch to account #1 globally
  gitswitch --local 2          # Switch to account #2 locally
```

[^1]: if you use a version manager like asdf, you may need to reshim to make the command available.