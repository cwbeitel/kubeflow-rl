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

DEPLOY=${1:-1}

SALT=`date | shasum -a 256 | cut -c1-8`
ENV_TAG=gcr.io/kubeflow-rl/fission-python-kube:0.0.1-$SALT

docker build -t ${ENV_TAG} .

if [[ $DEPLOY == 1 ]]; then

  gcloud docker -- push ${ENV_TAG}

  if [[ `fission env list | grep fission-python-kube` ]]; then
    fission env update --name python-kube --image ${ENV_TAG}
  else
    fission env create --name python-kube --image ${ENV_TAG}
  fi

fi
