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
FUNCTION_NAME=job-trigger-${TRIGGER}
ROUTE_NAME=${FUNCTION_NAME}-events

# Upload your function code to fission
fission function update --name ${FUNCTION_NAME} --env python-kube --code ${TRIGGER}.py

# Test the function
# python nats-pub.py checkpoint-events -d "A checkpoint was written!"

# TODO: Get from the mq a message that confirms checkpoint-responder fired and
# parsed the message data.
# python nats-sub.py checkpoint-responder-events


curl -H "Content-Type: application/json" -X POST -d '{"args":{"render_count":2,"meta":{"elapsed_time":20.00865602493286,"global_step":1197},"log_dir":"gs://kubeflow-rl-kf/jobs/kuka-46613b75"},"job_type":"render"}' ${FISSION_ROUTER}/${ROUTE_NAME}

# curl -H "Content-Type: application/json" -X POST -d '{"job_type":"render","log_dir":"gs://kubeflow-rl-kf/jobs/pybullet-kuka-ff-0118-2346-bac2"}' ${FISSION_ROUTER}/${ROUTE_NAME}
