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

case $1 in
  start)
    # The --host 0.0.0.0 is important, otherwise it defaults to 127.0.0.1
    # and that doesn't work with docker-compose.
    # rm -fr config/kinto.ini
    # kinto init --backend memory --host 0.0.0.0 --port 9999
    kinto start --ini testkinto/kinto.ini --port 9999 ${@:2}
    # echo "WHAT?!"
    ;;
  initialize-kinto-wizard)
    kinto-wizard load ${@:2}
    ;;
  *)
    exec "$@"
    ;;
esac
