SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker run -it \
  -v ${SCRIPT_DIR}/trainer:/app/trainer \
  --entrypoint /usr/bin/env \
  gcr.io/kubeflow-rl/kubeflow-rl-agents:cpu-55d1a0ef \
  python -m trainer.task_test
