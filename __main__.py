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

"""Trampoline to make zipped directories runnable."""

# Prepend the "python" subdirectory to the path, allowing execution from
# a zip file copy of the entire repo. Note that this also works if the
# resulting path is in a zip file.
import os
import sys
mmrepo_path = os.path.join(os.path.dirname(__file__), "python")
sys.path.insert(0, mmrepo_path)

from mmrepo import main
main.main()
