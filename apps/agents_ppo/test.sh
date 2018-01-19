SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DOCKER_CMD="docker run -it \
  -v ${SCRIPT_DIR}/trainer:/app/trainer \
  -v /tmp/agents-logs/test:/tmp/agents-logs/test \
  --entrypoint /usr/bin/env \
  gcr.io/kubeflow-rl/agents-ppo:cpu-6ff68cdb \
  python -m trainer.task_test"

echo "Running test with docker command:"
echo ${DOCKER_CMD}

eval ${DOCKER_CMD}

# 1.4.1, agents-distributed: gcr.io/kubeflow-rl/agents-ppo:cpu-6ff68cdb
# 1.4.1: gcr.io/kubeflow-rl/base-agents:cpu-10593c96

# 1.5.0-rc1: gcr.io/kubeflow-rl/agents-ppo:cpu-60d01606

# 1.3.0, agents-distributed: gcr.io/kubeflow-rl/agents-ppo:cpu-ebf56849
# 1.3.0: gcr.io/kubeflow-rl/kubeflow-rl-agents:cpu-55d1a0ef
