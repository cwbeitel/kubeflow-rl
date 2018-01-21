# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# TODO: Assumes user has kubeless cli installed.
if ${KUBELESS_OR_FISSION} == "kubeless"; then
if [[ -z $(which kubeless) ]]; then
  echo "It looks like the Kubeless CLI is not installed on your machine."
  echo "Please install it before proceeding, see"
  echo "https://github.com/kubeless/kubeless"
  exit 1
fi

kubeless function deploy checkpoint-responder --runtime python2.7 \
                                --handler responder_kubeless.main \
                                --from-file responder_kubeless.py \
                                --trigger-topic checkpoint-events

kubeless topic create checkpoint-events

kubeless topic publish --topic checkpoint-events --data "Hello World!"
