help:
	@echo "Welcome to Buildhub\n"
	@echo "  run                         start everything"
	@echo "  clean                       delete local files"
	@echo "  stop                        stop any docker containers"
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

clean:
	rm -fr lambda.zip
	rm -fr .docker-build
	rm -fr .metadata*.json

run:
	docker-compose up

stop:
	docker-compose stop

build:
	docker-compose build buildhub
	touch .docker-build

functional-tests:
	docker-compose up -d testkinto
	./bin/wait-for localhost:9999
	docker-compose run kinto initialize-kinto-wizard jobs/buildhub/initialization.yml  --server http://testkinto:9999/v1 --auth user:pass
	docker-compose run buildhub functional-tests
	docker-compose stop

unit-tests: .docker-build
	docker-compose run buildhub unit-tests

lambda.zip: .docker-build
	docker-compose run buildhub lambda.zip

upload-to-s3:
	echo "NotImplemented" && exit 1
	# $(PYTHON) bin/upload_to_s3.py

docs:
	docker-compose run docs build

lintcheck: .docker-build
	docker-compose run buildhub lintcheck
	# docker-compose run ui lintcheck

shell:
	docker-compose run buildhub bash

sudo-shell:
	docker-compose run --user 0 buildhub bash

psql:
	docker-compose run db psql -h db -U postgres
