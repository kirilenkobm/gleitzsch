#!/bin/sh
find . -name "*.swift" -exec echo "{}:" \; -exec cat "{}" \;
