SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker run -it \
  -v ${SCRIPT_DIR}/trainer:/app/trainer \
  --entrypoint /usr/bin/env \
  gcr.io/kubeflow-rl/agents-ppo:cpu-35b63fae \
  python -m trainer.task_test

# 1.4.1, agents-distributed: gcr.io/kubeflow-rl/agents-ppo:cpu-35b63fae
# 1.4.1: gcr.io/kubeflow-rl/base-agents:cpu-10593c96

# 1.5.0-rc1: gcr.io/kubeflow-rl/agents-ppo:cpu-60d01606

# 1.3.0, agents-distributed: gcr.io/kubeflow-rl/agents-ppo:cpu-ebf56849
# 1.3.0: gcr.io/kubeflow-rl/kubeflow-rl-agents:cpu-55d1a0ef
