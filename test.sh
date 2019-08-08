#!/usr/bin/env bash

mkdir -p .venv
virtualenv .venv -p python3
. .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
echo ""
echo ""
echo ""
echo "**********UNIT TEST***********"
cd test/unit
PYTHONPATH=../../src python -m unittest discover --verbose

echo ""
echo ""
echo ""
echo "**********INTEGRATION TEST***********"
cd ../integration
PYTHONPATH=../../src python -m unittest discover --verbose

deactivate