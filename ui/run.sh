#!/usr/bin/env bash
set -eo pipefail

usage() {
  echo "usage: ./bin/run.sh start|outdated|lintcheck"
  echo ""
  echo "    start                         Start React dev server"
  echo "    outdated                      List npm packages that are outdated"
  echo "    lintcheck                     Prettier check all the source files"
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
    # Replace this (and consider that lint_problem.sh)
    # because if this errors it's really ugly and hard to read since you
    # get a bunch of "npm errors".
    yarn run cs-check
    ;;
  *)
    exec "$@"
    ;;
esac
