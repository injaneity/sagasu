all:config

start:
	@echo "executing main program..."
	python3 do.py

config:.pre-commit-config.yaml
	@echo "installing precommit hooks..."
	pip install pre-commit
	pre-commit install
