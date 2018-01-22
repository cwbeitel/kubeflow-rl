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

# 1.4.1, agents-distributed
# FROM gcr.io/kubeflow-rl/base-agents-distributed:cpu-f97ee488
# FROM gcr.io/kubeflow-rl/base-agents-distributed:cpu-b95365fe

# 1.4.1
FROM gcr.io/kubeflow-rl/base-agents:cpu-10593c96

# 1.3.0, agents-distributed
# FROM gcr.io/kubeflow-rl/base-agents-distributed:cpu-6ac03904

# 1.3.0
# FROM gcr.io/kubeflow-rl/base-agents:cpu-3c4cc9bd

# 1.5.0-rc1
# FROM gcr.io/kubeflow-rl/agents-ppo:cpu-60d01606

# Hack
RUN pip install google-cloud-storage==1.7.0

ADD trainer /app/trainer/

# TODO: Split demo stuff out into separate container?
ADD * /app/demo/

WORKDIR /app/

ENTRYPOINT ["python", "-m", "trainer.task"]
