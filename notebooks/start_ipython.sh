#!/bin/sh
# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")
# Absolute path of the project directory
PROJECT_DIR=$(dirname "$SCRIPTPATH")
PYTHONPATH="$PROJECT_DIR":$PYTHONPATH ipython notebook