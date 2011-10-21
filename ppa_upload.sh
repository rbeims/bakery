#!/bin/sh

version=`grep -e '^version = ' setup.py|sed -e "s%.*'\(.*\)'.*%\1%;"`

#eval `gpg-agent --daemon`

LEAD_DISTRO="oneiric"
OLD_DISTROS="lucid maverick natty"

export DH_ALWAYS_EXCLUDE=.git

for distro in $LEAD_DISTRO $OLD_DISTROS ; do
  debchange --distribution ${distro} --newversion ${version}~${distro} -b ${distro} build
  debuild -S -sa
done

cd ..
for distro in $LEAD_DISTRO $OLD_DISTROS ; do
  dput ppa:esben-haabendal/oe-lite oe-lite_${version}~${distro}_source.changes
done
