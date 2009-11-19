#!/bin/sh
./setup.py bdist_egg -d ../dist sdist -d ../dist upload && ./setup.py clean --all
