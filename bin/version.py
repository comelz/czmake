import sys
import os
import subprocess
import argparse
from os.path import exists

def argv_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-O', '--c-output', help='path where to write the version.h header file', metavar='HEADER_FILE')
    parser.add_argument('-o', '--output', help='path where to write the VERSION file', metavar='VERSION_FILE')
    parser.add_argument('project_dir', type=str, nargs=1, help='path to the SVN checkout', metavar='PROJECT_DIRECTORY')
    args = parser.parse_args()
    return args

def getVersion(path):
    tag = None
    for L in subprocess.check_output(["svn", "info", path]).decode("utf-8").splitlines():
        if L.startswith("URL:"):
            if "tags" in L:
                tag = L.rsplit("tags/", 1)[-1]

    ver = open(sys.argv[3]).read().strip() if len(sys.argv) == 4 else ''

    if tag:
        if tag != ver:
            ver = ver + "T" + tag
    else:
        subver = subprocess.check_output(["svnversion", path]).decode("utf-8").strip().replace(":", "-")
        ver = ver + "pre-r" + subver
    return ver

def write_if_different(outfile, content):
    if not exists(outfile) or open(outfile, 'r').read() != content:
        open(outfile, 'w').write(content)

if __name__ == '__main__':
    args = argv_parse()
    ver = getVersion(args.project_dir[0])
    os.putenv("LANG", "C")
    if args.c_output:
        new = """
#ifndef FULL_VER
#define FULL_VER "%(ver)s"
#endif
        """
        write_if_different(args.c_output, new % {"ver" : ver})

    if args.output:
        write_if_different(args.output, ver)
    print(ver)

