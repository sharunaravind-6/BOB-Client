#!/bin/bash
# Run the javascript file using node and merge stderr into stdout
node "$1" 2>&1