#!/bin/bash
# build.sh - Optimizes the Python package installation for Vercel

echo "Running custom build script for Vercel deployment"
echo "Python version: $(python --version)"

# Install base dependencies
pip install -r requirements.txt

# Special handling for heavy packages
# Using a smaller version of opencv
pip uninstall -y opencv-python || true
pip install --no-cache-dir --only-binary=:all: opencv-python-headless==4.5.5.64

# Log installation sizes
echo "Package sizes:"
pip list --format=freeze | while read package; do
  package_name=$(echo $package | cut -d= -f1)
  size=$(pip show $package_name 2>/dev/null | grep -i size | awk '{print $2}')
  echo "$package_name: $size KB"
done

echo "Build completed" 