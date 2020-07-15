#!/bin/bash

TEST_MODULES="
  mmrepo.git
"

# Make sure we are using python3.
function probe_python() {
  local python_exe="$1"
  local found
  local command
  command="import sys
if sys.version_info.major >= 3: print(sys.executable)"
  set +e
  found="$("$python_exe" -c "$command")"
  if ! [ -z "$found" ]; then
    echo "$found"
  fi
}

python_exe=""
for python_candidate in python3 python; do
  python_exe="$(probe_python "$python_candidate")"
  if ! [ -z "$python_exe" ]; then
    break
  fi
done

# Setup python path.
td="$(dirname $(readlink -f $0))"
export PYTHONPATH="$td/python:$PYTHONPATH"

for testmod in $TEST_MODULES; do
  echo "RUNNING: $testmod"
  "$python_exe" -m "$testmod"
done
