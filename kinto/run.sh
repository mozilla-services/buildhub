#!/usr/bin/env bash
set -eo pipefail

usage() {
  echo "usage: ./bin/run.sh start|migrate|initialize-kinto-wizard"
  echo ""
  echo "    start                         Start Kinto server with memory backend"
  echo "    migrate                       Create the kinto database tables"
  echo "    initialize-kinto-wizard       Initialize a Kinto server for buildhub"
  echo ""
  exit 1
}


echo "THIS SHOULD WAIT TILL POSTGRES IS UP AND RUNNING." # Like Tecken


[ $# -lt 1 ] && usage

case $1 in
  start)
    kinto start --ini kinto/kinto.ini ${@:2}
    ;;
  migrate)
    kinto migrate --ini kinto/kinto.ini ${@:2}
    ;;
  initialize-kinto-wizard)
    kinto-wizard load ${@:2}
    ;;
  *)
    exec "$@"
    ;;
esac
