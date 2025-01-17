setup-local: .venv/.finished_venv_install local.env

local.env:
	cp local.env.example local.env
	echo "Copied example env file to local.env, please adapt"

# Adapted from https://github.com/mara/mara-app/blob/master/.scripts/install.mk
.venv/.finished_venv_install:
	mkdir -p .venv
	${PYTHON} -m virtualenv .venv
	echo "Setting up .venv"
	(cd .venv && ${PYTHON} -m venv .)
	.venv/${PYTHON_VENV}${PYTHON} -m pip install --upgrade pip pipdeptree
	.venv/${PYTHON_VENV}${PYTHON} -m pip install --requirement=requirements.txt.freeze
	touch $@


update-packages: .venv/.finished_venv_install
	.venv/${PYTHON_VENV}${PYTHON} -m pip install --requirement=requirements.txt --upgrade
	.venv/${PYTHON_VENV}pipdeptree --warn=fail
	.venv/${PYTHON_VENV}${PYTHON} -m pip freeze | grep -v "pkg-resources" > requirements.txt.freeze
	echo "Updated all packages, please run tests to ensure not breakage!"
