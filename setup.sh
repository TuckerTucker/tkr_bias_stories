#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.
set -u  # Treat unset variables as an error when substituting.

# Logging function
log() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Function to install requirements from a file
install_requirements() {
    local req_file="$1"
    if [[ -f "${req_file}" ]]; then
        log "Installing requirements from ${req_file}"
        pip install -r "${req_file}" || {
            echo "[ERROR] Failed to install requirements from ${req_file}. Exiting."
            exit 1
        }
    else
        echo "[ERROR] ${req_file} not found. Skipping."
    fi
}

# Array of packages to clone
packages=("tkr_utils" "tkr_env")

# Check and clone each package
for package in "${packages[@]}"; do
    if [[ -d "${package}" ]]; then
        log "Package ${package} already exists, skipping clone"
    else
        log "Cloning package: ${package}"
        git clone "http://github.com/tuckertucker/${package}" || {
            echo "[ERROR] Failed to clone ${package}. Exiting."
            exit 1
        }
    fi
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

# Install requirements from tkr_utils
install_requirements "tkr_utils/requirements.txt"

# Install requirements from project root
install_requirements "requirements.txt"

# Install UI dependencies
if [[ -d "ui" ]]; then
    log "Installing UI dependencies"
    cd ui
    npm install || {
        echo "[ERROR] Failed to install UI dependencies. Exiting."
        exit 1
    }
    cd ..
else
    echo "[ERROR] UI directory not found. Skipping npm install."
fi

log "Setup completed successfully."
