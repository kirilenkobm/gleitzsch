#!/bin/sh
echo "README.md:"
cat README.md
find . -name "*.swift" -exec echo "{}:" \; -exec cat "{}" \;
find . -name "*.metal" -exec echo "{}:" \; -exec cat "{}" \;
