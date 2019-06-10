# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

.PHONY: help
help: default

.PHONY: default
default:
	@echo "Welcome to Buildhub\n"
	@echo "  build                       build buildhub Docker image"
	@echo "  run                         start everything"
	@echo "  clean                       delete local files"
	@echo "  stop                        stop any docker containers"
	@echo ""
	@echo "  functional-tests            run the functional tests"
	@echo "  unit-tests                  run the pure python unit tests"
	@echo "  lambda.zip                  build lambda.zip from within the container"
	@echo "  lintcheck                   run lint checking (i.e. flake8)"
	@echo "  upload-to-s3                upload lambda.zip to AWS"
	@echo "  shell                       enter a bash shell with volume mount"
	@echo "  sudo-shell                  enter a bash shell, as root, with volume mount"
	@echo "  psql                        open the psql cli"
	@echo "\n"

.docker-build:
	make build

.PHONY: clean
clean:
	rm -fr lambda.zip
	rm -fr .docker-build
	rm -fr .metadata*.json

.PHONY: run
run:
	docker-compose up

.PHONY: stop
stop:
	docker-compose stop

.PHONY: build
build:
	docker-compose build buildhub
	touch .docker-build

.PHONY: functional-tests
functional-tests:
	docker-compose up -d testkinto
	./bin/wait-for localhost:9999
	docker-compose run kinto initialize-kinto-wizard jobs/buildhub/initialization.yml  --server http://testkinto:9999/v1 --auth user:pass
	docker-compose run buildhub functional-tests
	docker-compose stop

.PHONY: unit-tests
unit-tests: .docker-build
	docker-compose run buildhub unit-tests

lambda.zip: .docker-build
	docker-compose run buildhub lambda.zip

.PHONY: upload-to-s3
upload-to-s3:
	echo "NotImplemented" && exit 1
	# $(PYTHON) bin/upload_to_s3.py

.PHONY: docs
docs:
	docker-compose run docs build

.PHONY: lintcheck
lintcheck: .docker-build
	docker-compose run buildhub lintcheck
	# docker-compose run ui lintcheck

.PHONY: shell
shell:
	docker-compose run buildhub bash

.PHONY: sudo-shell
sudo-shell:
	docker-compose run --user 0 buildhub bash

.PHONY: psql
psql:
	docker-compose run db psql -h db -U postgres
