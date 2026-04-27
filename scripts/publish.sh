#!/bin/bash
# Publish ErTing to PyPI

set -e

echo "Cleaning old distributions..."
rm -rf dist/

echo "Building package..."
python -m build

echo "Uploading to PyPI..."
twine upload dist/*

echo "Done!"
