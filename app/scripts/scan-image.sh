#!/usr/bin/env bash
set -euo pipefail

# Create the virtual environment
venvDir="ggshield"
python3 -m venv ${venvDir}
source ${venvDir}/bin/activate

PIP_INDEX_URL="https://${ARTIFACTORY_USERNAME}:${ARTIFACTORY_ACCESS_TOKEN}@${ARTIFACTORY_HOSTNAME}/artifactory/api/pypi/iress-pypi/simple"

pip3 install -U wheel
pip3 install -U ggshield

python3 ${venvDir}/bin/ggshield scan docker ${IMAGE_NAME_TAG}

deactivate