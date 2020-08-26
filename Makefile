SHELL := /bin/bash
########################################################################################################################
##
## Makefile for managing project
##
########################################################################################################################
THIS_FILE := $(lastword $(MAKEFILE_LIST))
activate = VIRTUAL_ENV_DISABLE_PROMPT=true . .venv/bin/activate;
env?=dev
docker_tag?= dev

ensure-venv:
ifeq ($(wildcard .venv),)
	@$(MAKE) -f $(THIS_FILE) venv
endif

venv:
	if [ -d .venv ]; then rm -rf .venv; fi
	python3.8 -m venv .venv --clear
	$(activate) pip3 install --upgrade pip

init: ensure-venv
	$(activate) pip3 install -r requirements.txt --use-feature=2020-resolver

lambda:
	$(activate) ./export_lambda.py  $(args)

dynamo:
	$(activate) ./export_dynamodb.py  $(args)