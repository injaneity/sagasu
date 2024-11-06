all:start

start:
	python3 -m bot.bot

config:.pre-commit-config.yaml
	@echo "installing precommit hooks..."
	pip install pre-commit
	pre-commit install
	pre-commit autoupdate
	pre-commit run --all-files
	pip install python-telegram-bot