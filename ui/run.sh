#!/usr/bin/env bash
set -eo pipefail

usage() {
  echo "usage: ./run.sh start|outdated|lintcheck|lintfix"
  echo ""
  echo "    start                         Start React dev server"
  echo "    outdated                      List npm packages that are outdated"
  echo "    lintcheck                     Prettier check all the source files"
  echo "    lintfix                       Let Prettier fix all source files"
  echo ""
  exit 1
}

[ $# -lt 1 ] && usage


case $1 in
  start)
    yarn run start | cat
    ;;
  outdated)
    yarn outdated
    ;;
  lintcheck)
    yarn run lint:prettier
    ;;
  lintfix)
    yarn run lint:prettierfix
    ;;
  *)
    exec "$@"
    ;;
esac
