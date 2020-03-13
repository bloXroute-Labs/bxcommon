#!/usr/bin/env bash

mkdir -p .venv
virtualenv .venv -p python3
. .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r requirements-optional.txt

echo ""
echo ""
echo ""
echo "**********TYPE CHECKING***********"
pyre check
