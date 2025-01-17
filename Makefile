# Use some sensible default shell settings
SHELL := /bin/bash
.ONESHELL:
.SILENT:

RED='\033[1;31m'
CYAN='\033[0;36m'
NC='\033[0m'

.PHONY: run
run:
	cd app/cmd;make