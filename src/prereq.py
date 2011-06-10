"""
Provides a warning and error code if python version isn't compatible.
"""

import os
import sys
import shutil
import tempfile

TORCTL_REPO = "git://git.torproject.org/pytorctl.git"
CAGRAPH_TARBALL_URL = "http://cagraph.googlecode.com/files/cagraph-1.2.tar.gz"
CAGRAPH_TARBALL_NAME = "cagraph-1.2.tar.gz"
CAGRAPH_TARBALL_ROOT = "cagraph-1.2"

def isTorCtlAvailable():
  """
  True if TorCtl is already available on the platform, false otherwise.
  """
  
  try:
    import TorCtl
    return True
  except ImportError:
    return False

def isCagraphAvailable():
  """
  True if cagraph is already available on the platform, false otherwise.
  """
  try:
    import cagraph
    return True
  except ImportError:
    return False

def promptTorCtlInstall():
  """
  Asks the user to install TorCtl. This returns True if it was installed and
  False otherwise (if it was either declined or failed to be fetched).
  """
  
  userInput = raw_input("Arm requires TorCtl to run, but it's unavailable. Would you like to install it? (y/n): ")
  
  # if user says no then terminate
  if not userInput.lower() in ("y", "yes"): return False
  
  # attempt to install TorCtl, printing the issue if unsuccessful
  try:
    installTorCtl()
    
    if not isTorCtlAvailable():
      raise IOError("Unable to install TorCtl, sorry")
    
    print "TorCtl successfully installed"
    return True
  except IOError, exc:
    print exc
    return False

def promptCagraphInstall():
  """
  Asks the user to install cagraph. This returns True if it was installed and
  False otherwise (if it was either declined or failed to be fetched).
  """
  
  userInput = raw_input("Arm requires cagraph to run, but it's unavailable. Would you like to install it? (y/n): ")
  
  # if user says no then terminate
  if not userInput.lower() in ("y", "yes"): return False
  
  # attempt to install cagraph, printing the issue if unsuccessful
  try:
    installCagraph()
    
    if not isCagraphAvailable():
      raise IOError("Unable to install cagraph, sorry")
    
    print "cagraph successfully installed"
    return True
  except IOError, exc:
    print exc
    return False

def installTorCtl():
  """
  Checks out the current git head release for TorCtl and bundles it with arm.
  This raises an IOError if unsuccessful.
  """
  
  if isTorCtlAvailable(): return
  
  # temporary destination for TorCtl's git clone, guarenteed to be unoccupied
  # (to avoid conflicting with files that are already there)
  tmpFilename = tempfile.mktemp("/torctl")
  
  # fetches TorCtl
  exitStatus = os.system("git clone --quiet %s %s > /dev/null" % (TORCTL_REPO, tmpFilename))
  if exitStatus: raise IOError("Unable to get TorCtl from %s. Is git installed?" % TORCTL_REPO)
  
  # the destination for TorCtl will be our directory
  ourDir = os.path.dirname(os.path.realpath(__file__))
  
  # exports TorCtl to our location
  exitStatus = os.system("(cd %s && git archive --format=tar --prefix=TorCtl/ master) | (cd %s && tar xf - 2> /dev/null)" % (tmpFilename, ourDir))
  if exitStatus: raise IOError("Unable to install TorCtl to %s" % ourDir)
  
  # Clean up the temporary contents. This isn't vital so quietly fails in case
  # of errors.
  shutil.rmtree(tmpFilename, ignore_errors=True)

def installCagraph():
  """
  Downloads and extracts the cagraph tarball.
  This raises an IOError if unsuccessful.
  """
  
  if isCagraphAvailable(): return
  
  tmpDir = tempfile.mkdtemp()
  tmpFilename = os.path.join(tmpDir, CAGRAPH_TARBALL_NAME)
  
  exitStatus = os.system("wget -P %s %s" % (tmpDir, CAGRAPH_TARBALL_URL))
  if exitStatus: raise IOError("Unable to fetch cagraph from %s. Is wget installed?" % CAGRAPH_TARBALL_URL)
  
  # the destination for cagraph will be our directory
  ourDir = os.path.dirname(os.path.realpath(__file__))
  
  # exports cagraph to our location
  exitStatus = os.system("(cd %s && tar --strip-components=1 -xzf %s %s/cagraph)" % (ourDir, tmpFilename, CAGRAPH_TARBALL_ROOT))
  if exitStatus: raise IOError("Unable to extract cagraph to %s" % ourDir)
  
  # Clean up the temporary contents. This isn't vital so quietly fails in case
  # of errors.
  shutil.rmtree(tmpDir, ignore_errors=True)

def allPrereq():
  """
  Requrements for both the cli and gui versions of arm.
  """
  
  majorVersion = sys.version_info[0]
  minorVersion = sys.version_info[1]
  
  if majorVersion > 2:
    print("arm isn't compatible beyond the python 2.x series\n")
    sys.exit(1)
  elif majorVersion < 2 or minorVersion < 5:
    print("arm requires python version 2.5 or greater\n")
    sys.exit(1)
  
  if not isTorCtlAvailable():
    isInstalled = promptTorCtlInstall()
    if not isInstalled: sys.exit(1)

def cliPrereq():
  """
  Requirements for the cli arm interface.
  """
  
  allPrereq()
  
  try:
    import curses
  except ImportError:
    print("arm requires curses - try installing the python-curses package\n")
    sys.exit(1)

def guiPrereq():
  """
  Requirements for the gui arm interface.
  """
  
  allPrereq()
  
  try:
    import gtk
  except ImportError:
    print("arm requires gtk - try installing the python-gtk2 package\n")
    sys.exit(1)
  
  if not isCagraphAvailable():
    isInstalled = promptCagraphInstall()
    if not isInstalled: sys.exit(1)

if __name__ == '__main__':
  isGui = "-g" in sys.argv or "--gui" in sys.argv
  if isGui: guiPrereq()
  else: cliPrereq()

