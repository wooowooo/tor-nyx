#!/usr/bin/env python
import os
import sys
import gzip
import tempfile
from src.version import VERSION
from distutils.core import setup

# Use 'tor-arm' instead of 'arm' in the path for the sample armrc if we're
# building for debian.

isDebInstall = False
for arg in sys.argv:
  if "tor-arm" in arg or "release_deb" in arg:
    isDebInstall = True
    break

docPath = "/usr/share/doc/%s" % ("tor-arm" if isDebInstall else "arm")

# Allow the docPath to be overridden via a '--docPath' argument. This is to
# support custom documentation locations on Gentoo, as discussed in:
# https://bugs.gentoo.org/349792

try:
  docPathFlagIndex = sys.argv.index("--docPath")
  if docPathFlagIndex < len(sys.argv) - 1:
    docPath = sys.argv[docPathFlagIndex + 1]
    
    # remove the custom --docPath argument (otherwise the setup call will
    # complain about them)
    del sys.argv[docPathFlagIndex:docPathFlagIndex + 3]
  else:
    print "No path provided for --docPath"
    sys.exit(1)
except ValueError: pass # --docPath flag not found

# Provides the configuration option to install to "/usr/share" rather than as a
# python module. Alternatives are to either provide this as an input argument
# (not an option for deb/rpm builds) or add a setup.cfg with:
#   [install]
#   install-purelib=/usr/share
# which would mean a bit more unnecessary clutter.

manFilename = "arm.1"
if "install" in sys.argv:
  sys.argv += ["--install-purelib", "/usr/share"]
  
  # Compresses the man page. This is a temporary file that we'll install. If
  # something goes wrong then we'll print the issue and use the uncompressed man
  # page instead.
  
  try:
    manInputFile = open('arm.1', 'r')
    manContents = manInputFile.read()
    manInputFile.close()
    
    # temporary destination for the man page guarenteed to be unoccupied (to
    # avoid conflicting with files that are already there)
    tmpFilename = tempfile.mktemp("/arm.1.gz")
    
    # make dir if the path doesn't already exist
    baseDir = os.path.dirname(tmpFilename)
    if not os.path.exists(baseDir): os.makedirs(baseDir)
    
    manOutputFile = gzip.open(tmpFilename, 'wb')
    manOutputFile.write(manContents)
    manOutputFile.close()
    
    # places in tmp rather than a relative path to avoid having this copy appear
    # in the deb and rpm builds
    manFilename = tmpFilename
  except IOError, exc:
    print "Unable to compress man page: %s" % exc

# When installing we include a bundled copy of TorCtl. However, when creating
# a deb we have a dependency on the python-torctl package instead:
# http://packages.debian.org/unstable/main/python-torctl
installPackages = ['arm', 'arm.interface', 'arm.interface.graphing', 'arm.interface.connections', 'arm.util']
if not isDebInstall: installPackages.append('arm.TorCtl')

setup(name='arm',
      version=VERSION,
      description='Terminal tor status monitor',
      license='GPL v3',
      author='Damian Johnson',
      author_email='atagar@torproject.org',
      url='http://www.atagar.com/arm/',
      packages=installPackages,
      package_dir={'arm': 'src'},
      data_files=[("/usr/bin", ["arm"]),
                  ("/usr/share/man/man1", [manFilename]),
                  (docPath, ["armrc.sample"]),
                  ("/usr/share/arm", ["src/settings.cfg"])],
     )

# Cleans up the temporary compressed man page.
if manFilename != 'arm.1' and os.path.isfile(manFilename):
  if "-q" not in sys.argv: print "Removing %s" % manFilename
  os.remove(manFilename)

# Removes the egg_info file. Apparently it is not optional during setup
# (hardcoded in distutils/command/install.py), nor are there any arguments to
# bypass its creation. The deb build removes this as part of its rules script.
eggPath = '/usr/share/arm-%s.egg-info' % VERSION

if not isDebInstall and os.path.isfile(eggPath):
  if "-q" not in sys.argv: print "Removing %s" % eggPath
  os.remove(eggPath)

