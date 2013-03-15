#!/bin/sh

version=`./setup.py --version`
build_version=1

eval `gpg-agent --daemon`

LEAD_DISTRO="precise"
OLD_DISTROS="lucid maverick natty oneiric quantal"

export DH_ALWAYS_EXCLUDE=.git

for distro in $LEAD_DISTRO $OLD_DISTROS ; do
  echo "Building for $distro"
  if [ -e debian/control.$distro ] ; then
    ln -sf control.$distro debian/control
  else
    ln -sf control.common debian/control
  fi
  debchange --distribution ${distro} --newversion ${version}~${distro}${build_version} -b ${distro} build
  debuild -S -k5B997C4F -sa
  echo
done

cd ..
for distro in $LEAD_DISTRO $OLD_DISTROS ; do
  print "Uploading $distro"
  dput ppa:esben-haabendal/oe-lite oe-lite_${version}~${distro}${build_version}_source.changes
done
