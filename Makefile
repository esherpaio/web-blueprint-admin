.PHONY: commit
commit:
	git rev-parse --short HEAD

.PHONY: venv packages
venv:
	python3.12 -m venv .venv
packages:
	pip install --upgrade pip
	pip freeze | grep '^web-' | sed 's/ @.*//' | xargs -r pip uninstall -y
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

.PHONY: format format-py format-html
format: format-py format-html
format-py:
	ruff check . --fix
	ruff format .
format-html:
	djlint . --reformat

.PHONY: lint lint-py lint-html
lint: lint-py lint-html
lint-py:
	ruff check .
	ruff format . --check
	mypy --install-types --non-interactive .
lint-html:
	djlint . --check

.PHONY: test
test:
	pytest --maxfail=1 --verbose
