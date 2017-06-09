#!/bin/bash

find . -maxdepth 2 -type d -name ".git" -exec dirname {} \; -exec git -C {} rev-parse -q HEAD \; -exec echo \;
