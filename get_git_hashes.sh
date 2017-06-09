#!/bin/bash

find . -maxdepth 1 -type d -exec echo -e "\033[7m" {} ":\033[0m" \; -exec git -C {} rev-parse HEAD \;
