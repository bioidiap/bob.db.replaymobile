#!/usr/bin/env bash
# Mon  8 Aug 17:40:24 2016 CEST

# Creates a build environment for the current package
# $1 == conda folder (e.g. "/opt/conda")
# $2 == python version (e.g. "2.7")
# $3 == local dir for environment (e.g. "env")

if [ "${#}" -ne 3 ]; then
  echo "usage: ${0} <conda-root> <python-version> <prefix>"
  echo "example: ${0} /opt/conda 2.7 env"
  exit 1
fi

CONDA_FOLDER=${1}
PYTHON_VERSION=${2}
PREFIX=`pwd`/${3}
WHEELS_SERVER="www.idiap.ch"
WHEELS_REPOSITORY="https://${WHEELS_SERVER}/software/bob/wheels/gitlab/"

# Determines the architecture we're using
if [ "$(uname)" == "Darwin" ]; then
  ARCH="macosx"
else
  ARCH="linux"
fi

# Function for running command and echoing results
run_cmd() {
  echo "[(`date +%c`)>>] Running \"${@}\"..."
  ${@}
  if [ "$?" != "0" ]; then
    echo "[(`date +%c`)!!] Command Failed \"${@}\""
    exit 1
  else
    echo "[(`date +%c`)<<] Finished comand \"${@}\""
  fi
}

# Clones the conda dev environment to use
if [ ! -d ${PREFIX} ]; then
  echo "[++] Downloading environment list into file \`env.txt'..."
  pyver=$(echo ${PYTHON_VERSION} | tr -d '.')
  curl --silent https://gitlab.idiap.ch/bob/bob.admin/raw/master/${ARCH}/devel-py${pyver}.txt > env.txt
  echo "[++] Bootstrapping conda installation at ${PREFIX}..."
  run_cmd ${CONDA_FOLDER}/bin/conda create --prefix ${PREFIX} --file env.txt --yes
  if [ "${ARCH}" == "macosx" ] && [ -e "${PREFIX}/lib/libjpeg.8.dylib" ]; then
    run_cmd install_name_tool -id @rpath/libjpeg.8.dylib ${PREFIX}/lib/libjpeg.8.dylib
  fi
  run_cmd ${CONDA_FOLDER}/bin/conda clean --lock
else
  echo "[!!] Prefix directory ${PREFIX} exists, not re-installing..."
fi

# Source the newly created conda environment
echo "[>>] Running \"source ${CONDA_FOLDER}/bin/activate ${PREFIX}\"..."
source ${CONDA_FOLDER}/bin/activate ${PREFIX}
echo "[<<] Environment ${PREFIX} activated"

# Verify where pip is installed
use_pip=`which pip`
if [ -z "${use_pip}" ]; then
  echo "[!!] Cannot find pip, aborting..."
  exit 1
else
  echo "[++] Using pip: ${use_pip}"
fi

use_python=`which python`
if [ -z "${use_python}" ]; then
  echo "[!!] Cannot find python, aborting..."
  exit 1
else
  echo "[++] Using python: ${use_python}"
fi

# Install this package's build dependencies
if [ -e requirements.txt ]; then
  run_cmd ${use_pip} install --find-links ${WHEELS_REPOSITORY} --trusted-host ${WHEELS_SERVER}  --requirement requirements.txt
else
  echo "[!!] No requirements.txt file found, skipping 'pip install <build-deps>'..."
fi

# Install this package's test dependencies
if [ -e test-requirements.txt ]; then
  run_cmd ${use_pip} install --find-links ${WHEELS_REPOSITORY} --trusted-host ${WHEELS_SERVER} --requirement test-requirements.txt
else
  echo "[!!] No test-requirements.txt file found, skipping 'pip install <test-deps>'..."
fi

# Finally, bootstrap the installation from the new environment
if [ -e bootstrap-buildout.py ]; then
  run_cmd ${use_python} bootstrap-buildout.py
else
  echo "[!!] No bootstrap-buildout.py file found, skipping 'buildout bootstrap'..."
fi
