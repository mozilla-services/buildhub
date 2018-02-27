VIRTUALENV = virtualenv --python=python3.6
VENV := $(shell echo $${VIRTUAL_ENV-.venv})
DOC_STAMP = $(VENV)/.doc_env_installed.stamp
PYTHON = $(VENV)/bin/python3
SPHINX_BUILDDIR = docs/_build

help:
	@echo "  clean                       delete local files"
	@echo "  build                       build the Docker™ image"
	@echo "  test                        run the tests from within the container"
	@echo "  lambda.zip                  build lambda.zip from within the container"
	@echo "  lintcheck                   run lint checking (i.e. flake8)"
	@echo "  upload-to-s3                upload lambda.zip to AWS"
	@echo "  docs                        build the project docs"
	@echo "  shell                       enter a bash shell with volume mount"

#
# virtualenv: $(PYTHON)
# $(PYTHON):
# 	$(VIRTUALENV) $(VENV) --python=python3.6

.docker-build:
	make build

clean:
	rm -fr lambda.zip
	rm -fr .docker-build

build:
	echo "{\"name\":\"buildhub\",\"commit\":`git rev-parse HEAD`\"}" > version.json
	docker build -t mozilla/buildhub .
	touch .docker-build

test:
	# docker run -it mozilla/buildhub test
	docker run -v `pwd`:/app -it app test

lambda.zip: .docker-build
	docker run -v `pwd`:/app --user 0 -it app lambda.zip
	cp lambda.zip buildhub-lambda-`git describe`.zip

upload-to-s3:
	$(PYTHON) bin/upload_to_s3.py

install-docs: $(DOC_STAMP)
$(DOC_STAMP): $(PYTHON) docs/requirements.txt
	$(VENV)/bin/pip install -Ur docs/requirements.txt
	touch $(DOC_STAMP)

docs: install-docs
	$(VENV)/bin/sphinx-build -a -W -n -b html -d $(SPHINX_BUILDDIR)/doctrees docs $(SPHINX_BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(SPHINX_BUILDDIR)/html/index.html"

lintcheck: .docker-build
	docker run -v `pwd`:/app -it app lintcheck

shell: .docker-build
	docker run -v `pwd`:/app -it app bash
