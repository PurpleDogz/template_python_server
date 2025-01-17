#!/bin/bash

exists()
{
  command -v "$1" >/dev/null 2>&1
}

PIP=pip3
PYTHON=python3

if ! exists $PIP; then
    PIP=pip
fi

if ! exists $PYTHON; then
    PYTHON=python
fi

$PIP install pyyaml > /dev/null 2>&1

yaml() {
    $PYTHON -c "import yaml;print(yaml.safe_load(open('$1'))$2)"
}

yaml_check() {
    $PYTHON -c "import yaml; y = yaml.safe_load(open('$1')); print(\"TRUE\") if $2 in y.keys() else print(\"FALSE\")"
}

yaml_array() {
    $PYTHON -c "import yaml;arr = yaml.safe_load(open('$1'))$2;print(*arr)"
}