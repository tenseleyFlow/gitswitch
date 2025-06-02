.PHONY: help install uninstall clean reinstall reshim

# Show help for each command
help:
	@echo "Gitswitch Makefile"
	@echo "  make install      - pip install -e . && asdf reshim python"
	@echo "  make uninstall    - pip uninstall gitswitch"
	@echo "  make clean        - rm -rf **/*/*.egg-info"
	@echo "  make reshim       - asdf reshim python"
	@echo "  make reinstall    - Uninstall, clean, then install & reshim"

install:
	pip install -e .
	asdf reshim python

uninstall:
	pip uninstall -y gitswitch

clean:
	rm -rf **/*/*.egg-info

reshim:
	asdf reshim python

reinstall: uninstall clean install

# Optionally add:
test:
	pytest tests/
