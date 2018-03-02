#!/usr/bin/env bash
set -eo pipefail

usage() {
  echo "usage: ./bin/run.sh start|initialize-kinto-wizard"
  echo ""
  echo "    start                         Start Kinto server with memory backend"
  echo "    initialize-kinto-wizard       Initialize a Kinto server for buildhub"
  echo ""
  exit 1
}

[ $# -lt 1 ] && usage

# Temp debugging
echo "COMMAND (in kinto/run-kinto.sh): $1"

case $1 in
  start)
    # The --host 0.0.0.0 is important, otherwise it defaults to 127.0.0.1
    # and that doesn't work with docker-compose.
    [ -f config/kinto.ini ] || kinto init --backend memory --host 0.0.0.0
    kinto start ${@:2}
    ;;
  initialize-kinto-wizard)
    kinto-wizard load ${@:2}
    ;;
  *)
    exec "$@"
    ;;
esac
