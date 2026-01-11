#!/bin/bash
# Local CI script for Hash-CAD Flutter app
# Run this before committing to verify tests pass

set -e

# Navigate to flutter_app directory
cd "$(dirname "$0")/.."

echo "=== Flutter Local CI ==="
echo ""

# uncomment here to also check for coding issues
#echo ">>> Running Flutter Analysis..."
#flutter analyze --no-fatal-infos
#echo "Analysis complete."
#echo ""

echo ">>> Running Flutter Tests..."
flutter test --coverage
echo "Tests complete."
echo ""

echo "=== All checks passed! ==="
