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

TRIGGER=${1:-render}
RE_DEPLOY=${1:-1}
FUNCTION_NAME=job-trigger-${TRIGGER}
ROUTE_NAME=${FUNCTION_NAME}-events

if [[ ${RE_DEPLOY} == 1 ]]; then
  fission function delete --name ${FUNCTION_NAME}
  ROUTE_ID=`fission route list | grep ${ROUTE_NAME} | cut -f1 -d' '`
  if [[ ${ROUTE_ID} ]]; then
    fission route delete --name ${ROUTE_ID}
  fi
fi

# Upload your function code to fission
fission function create --name job-trigger-${TRIGGER} --env python-kube --code ${TRIGGER}.py

# Create a mq trigger for checkpoint events that triggers the responder
# fission mqtrigger create --function checkpoint-responder \
#     --topic checkpoint-events \
#     --resptopic checkpoint-responder-events

# HACK: For now, trigger with HTTP given issues with NATS
fission route create --method POST --url /${ROUTE_NAME} --function ${FUNCTION_NAME}
