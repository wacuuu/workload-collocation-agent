#!/bin/bash
echo "Only for development purposes!"
cd "$(dirname "$0")"
CONFIG=${CONFIG:-configs/extra/static_measurements.yaml}
python3 -mpipenv run sudo env PYTHONPATH=. `python3 -mpipenv --py` wca/main.py -c $PWD/$CONFIG --root
