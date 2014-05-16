#!/bin/bash
./env/bin/python -c "from docker_watcher.version import version_number; print 'Version', version_number"

echo "Running tests"
./env/bin/coverage run --include=docker_watcher/* tests/__init__.py
OUT=$?
if [ "$OUT" == "0" ]; then
    ./env/bin/coverage report -m --fail-under=90 docker_watcher/*.py
    OUT=$?
fi

exit $OUT
