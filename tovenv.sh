#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

virtualenv -p python3 venv
source venv/bin/activate
python3 -m pip install -r requirements.txt

