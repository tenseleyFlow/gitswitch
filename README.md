# gitswitch
(noun) : something clever someday

### what is this?
This is a little tool I use to manage and switch between git configs quicker as I somehow have 3 GH accounts.
Reads account details from a toml file in $HOME/.config/gitswitch/accounts.toml

Installation:
clone this repo and `cd` into it. From there run: `pip install -e .` and `gitswitch` is available in that environment[^1].  

Usage:
```
vgitswitch              # Interactive account switching
vgitswitch add          # Add a new account
vgitswitch remove       # Remove an account
vgitswitch list         # List all accounts
```

[^1]: if you use a version manager like asdf, you may need to reshim to make the command available.