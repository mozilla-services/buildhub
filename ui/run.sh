#!/usr/bin/env bash
set -eo pipefail

usage() {
  echo "usage: ./bin/run.sh start|outdated"
  echo ""
  echo "    start                         Start React dev server"
  echo "    outdated                      List npm packages that are outdated"
  echo ""
  exit 1
}

[ $# -lt 1 ] && usage


case $1 in
  start)
    npm run start | cat
    ;;
  outdated)
    npm outdated
    ;;
  *)
    exec "$@"
    ;;
esac
