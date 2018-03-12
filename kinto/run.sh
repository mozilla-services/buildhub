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

# XXX This should come from the environment
# DATABASE_URL="postgres://postgres@db/postgres"

case $1 in
  start)
    # The --host 0.0.0.0 is important, otherwise it defaults to 127.0.0.1
    # and that doesn't work with docker-compose.
    #[ -f config/kinto.ini ] || kinto init --backend postgresql --host 0.0.0.0
    kinto start --ini kinto/kinto.ini ${@:2}
    #env kinto.storage_url=$DATABASE_URL \
    #kinto.cache_url=$DATABASE_URL \
    #kinto.permission_url=$DATABASE_URL \
  #    kinto start  ${@:2}
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
