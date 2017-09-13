VIRTUALENV = virtualenv --python=python3.6
VENV := $(shell echo $${VIRTUAL_ENV-.venv})
DOC_STAMP = $(VENV)/.doc_env_installed.stamp
PYTHON = $(VENV)/bin/python3
SPHINX_BUILDDIR = docs/_build

help:
	@echo "  clean                       delete local files"
	@echo "  container                   build the Docker™ image"
	@echo "  lambda.zip                  build lambda.zip from within the container"
	@echo "  upload-to-s3                upload lambda.zip to AWS"
	@echo "  docs                        build the project docs"

virtualenv: $(PYTHON)
$(PYTHON):
	$(VIRTUALENV) $(VENV) --python=python3.6

clean:
	rm -fr $(VENV) lambda.zip

container:
	docker build -t buildhub .

lambda.zip: container
	docker rm buildhub || true
	docker run --name buildhub buildhub lambda.zip
	docker cp buildhub:/app/lambda.zip .

upload-to-s3: lambda.zip
	$(PYTHON) bin/upload_to_s3.py

install-docs: $(DOC_STAMP)
$(DOC_STAMP): $(PYTHON) docs/requirements.txt
	$(VENV)/bin/pip install -Ur docs/requirements.txt
	touch $(DOC_STAMP)

docs: install-docs
	$(VENV)/bin/sphinx-build -a -W -n -b html -d $(SPHINX_BUILDDIR)/doctrees docs $(SPHINX_BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(SPHINX_BUILDDIR)/html/index.html"
