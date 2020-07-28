#!/bin/bash

# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


TEST_MODULES="
  mmrepo.git
  mmrepo.version_map
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
