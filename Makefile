VIRTUALENV = virtualenv --python=python3.6
VENV := $(shell echo $${VIRTUAL_ENV-.venv})
DOC_STAMP = $(VENV)/.doc_env_installed.stamp
PYTHON = $(VENV)/bin/python3
SPHINX_BUILDDIR = docs/_build

help:
	@echo "  docs                        build the docs"

virtualenv: $(PYTHON)
$(PYTHON):
	$(VIRTUALENV) $(VENV)

clean:
	rm -fr venv $(VENV) lambda.zip

virtualenv:
	virtualenv $(VENV) --python=python3.6
	$(VENV)/bin/pip install jobs/

lambda.zip: zip
zip: clean virtualenv
	cd $(VENV)/lib/python3.6/site-packages/; zip -r ../../../../lambda.zip *

build_image:
	docker build -t buildhub .

get_zip: build_image
	docker rm buildhub || true
	docker run --name buildhub buildhub
	docker cp buildhub:/app/lambda.zip .

upload-to-s3: lambda.zip
	python upload_to_s3.py

install-docs: $(DOC_STAMP)
$(DOC_STAMP): $(PYTHON) docs/requirements.txt
	$(VENV)/bin/pip install -Ur docs/requirements.txt
	touch $(DOC_STAMP)

docs: install-docs
	$(VENV)/bin/sphinx-build -a -W -n -b html -d $(SPHINX_BUILDDIR)/doctrees docs $(SPHINX_BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(SPHINX_BUILDDIR)/html/index.html"
