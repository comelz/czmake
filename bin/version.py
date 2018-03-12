import sys
import os
import subprocess

def getVersion(path):
    tag = None
    for L in subprocess.check_output(["svn", "info", path]).decode("utf-8").splitlines():
        if L.startswith("URL:"):
            if "tags" in L:
                tag = L.rsplit("tags/", 1)[-1]

    ver = open(sys.argv[3]).read().strip() if len(sys.argv) == 4 else ''

    if tag:
        if tag != ver:
            ver = ver + "-T" + tag
    else:
        subver = subprocess.check_output(["svnversion", path]).decode("utf-8").strip().replace(":", "-")
        ver = ver + "-pre-r" + subver
    return ver

os.putenv("LANG", "C")

new = """#ifndef FULL_VER
#define FULL_VER "%(ver)s"
#endif

"""

basepath = os.path.dirname(sys.argv[1])
ver = getVersion(basepath)

outpath = sys.argv[2]

current = ''
try:
    f = open(outpath)
    current = f.read()
    f.close()
except IOError:
    pass

new = new % {"ver" : ver}
if current != new:
    f = open(outpath, "w")
    f.write(new % {"ver" : ver})
    f.close()
    #cpack_config_path = sys.argv[1] + '/CPackConfig.cmake'
    #f = open(cpack_config_path, 'r')
    #cpackfile = f.read().split('\n')
    #f.close()
    #f = open(cpack_config_path, 'w')
    #for line in cpackfile:
    #    if line.startswith('SET(CPACK_PACKAGE_VERSION'):
    #        line = 'SET(CPACK_PACKAGE_VERSION "%s")' % ver
    #    f.write(line + '\n')
    #f.close()
    
