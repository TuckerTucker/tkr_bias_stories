#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.
set -u  # Treat unset variables as an error when substituting.

# Logging function
log() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Array of packages to clone
packages=("tkr_utils" "tkr_env" "tkr_tests")

# Clone each package
for package in "${packages[@]}"; do
    log "Cloning package: ${package}"
    git clone "http://github.com/tuckertucker/${package}" || {
        echo "[ERROR] Failed to clone ${package}. Exiting."
        exit 1
    }
done

# Copy the start_env file to the project root
start_env_source="tkr_env/start_env.copyToParent"
start_env_destination="start_env"

if [[ -f "${start_env_source}" ]]; then
    log "Copying ${start_env_source} to ${start_env_destination}"
    cp "${start_env_source}" "${start_env_destination}" || {
        echo "[ERROR] Failed to copy start_env. Exiting."
        exit 1
    }
else
    echo "[ERROR] ${start_env_source} not found. Exiting."
    exit 1
fi

# Source the start_env
log "Sourcing ${start_env_destination}"
source "${start_env_destination}" || {
    echo "[ERROR] Failed to source ${start_env_destination}. Exiting."
    exit 1
}

# Install the required packages
requirements_file="tkr_utils/requirements.txt"
if [[ -f "${requirements_file}" ]]; then
    log "Installing requirements from ${requirements_file}"
    pip install -r "${requirements_file}" || {
        echo "[ERROR] Failed to install requirements. Exiting."
        exit 1
    }
else
    echo "[ERROR] ${requirements_file} not found. Exiting."
    exit 1
fi

log "Setup completed successfully."
