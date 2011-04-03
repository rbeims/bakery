#!/bin/sh

version=`grep -e '^version = ' setup.py|sed -e "s%.*'\(.*\)'.*%\1%;"`

#eval `gpg-agent --daemon`

LEAD_DISTRO="karmic"
OLD_DISTROS="jaunty intrepid hardy"

for distro in $LEAD_DISTRO $OLD_DISTROS ; do
  debchange --distribution ${distro} --newversion ${version}~${distro} -b ${distro} build
  debuild -S -sa
done

cd ..
for distro in $LEAD_DISTRO $OLD_DISTROS ; do
  dput oe-bakery oe-bakery_${version}~${distro}_source.changes
done
