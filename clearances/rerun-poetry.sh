#!/bin/bash

poetry env activate
poetry update

set -e  # Exit immediately if any command fails

# Check if Poetry is installed
echo "Checking for Poetry installation..."

poetry show --tree

POETRY_BIN=$(command -v poetry)

# If not found, try default install location
if [ -z "$POETRY_BIN" ]; then
    if [ -x "$HOME/.local/bin/poetry" ]; then
        POETRY_BIN="$HOME/.local/bin/poetry"
    else
        echo "Poetry is not installed. Installing Poetry..."
        curl -sSL https://install.python-poetry.org | python3 -
        export PATH="$HOME/.local/bin:$PATH"
        POETRY_BIN="$HOME/.local/bin/poetry"
    fi
fi

# Verify poetry binary
if [ ! -x "$POETRY_BIN" ]; then
    echo "Poetry installation failed or binary not found."
    exit 1
fi

echo "Using Poetry from: $POETRY_BIN"
"$POETRY_BIN" --version

# Install dependencies
if [ ! -f "poetry.lock" ]; then
    echo "No poetry.lock file found. Installing all dependencies..."
    "$POETRY_BIN"
else
    echo "poetry.lock found. Installing from lockfile..."
    "$POETRY_BIN"
fi

# Run Streamlit app
echo "Running the Streamlit app..."
"$POETRY_BIN" run streamlit run clearances.py

