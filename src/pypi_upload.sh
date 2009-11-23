#!/bin/sh
./setup.py bdist_egg -d ../dist sdist -d ../dist upload && ./setup.py clean --all
scp ../dist/oe-bakery-*.tar.gz dev.doredevelopment.dk:/srv/public/www/oe-bakery
