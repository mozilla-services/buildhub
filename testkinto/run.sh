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
    # Note that this kinto.ini is part of the code.
    kinto start --ini testkinto/kinto.ini --port 9999 ${@:2}
    ;;
  initialize-kinto-wizard)
    kinto-wizard load ${@:2}
    ;;
  *)
    exec "$@"
    ;;
esac
