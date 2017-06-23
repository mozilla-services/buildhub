VIRTUALENV = virtualenv --python=python3
VENV := $(shell echo $${VIRTUAL_ENV-.venv})
DOC_STAMP = $(VENV)/.doc_env_installed.stamp
PYTHON = $(VENV)/bin/python3
SPHINX_BUILDDIR = docs/_build

help:
	@echo "  docs                        build the docs"

virtualenv: $(PYTHON)
$(PYTHON):
	$(VIRTUALENV) $(VENV)

install-docs: $(DOC_STAMP)
$(DOC_STAMP): $(PYTHON) docs/requirements.txt
	$(VENV)/bin/pip install -Ur docs/requirements.txt
	touch $(DOC_STAMP)

docs: install-docs
	$(VENV)/bin/sphinx-build -a -W -n -b html -d $(SPHINX_BUILDDIR)/doctrees docs $(SPHINX_BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(SPHINX_BUILDDIR)/html/index.html"
