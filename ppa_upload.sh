#!/bin/sh

version=`grep -e '^version = ' setup.py|sed -e "s%.*'\(.*\)'.*%\1%;"`

#eval `gpg-agent --daemon`

LEAD_DISTRO="oneiric"
OLD_DISTROS="lucid maverick natty"

export DH_ALWAYS_EXCLUDE=.git

for distro in $LEAD_DISTRO $OLD_DISTROS ; do
  if [ -e debian/control.$distro ] ; then
    ln -sf control.$distro debian/control
  else
    ln -sf control.common debian/control
  fi
  debchange --distribution ${distro} --newversion ${version}~${distro} -b ${distro} build
  debuild -S -k5B997C4F -sa
done

cd ..
for distro in $LEAD_DISTRO $OLD_DISTROS ; do
  dput ppa:esben-haabendal/oe-lite oe-lite_${version}~${distro}_source.changes
done
