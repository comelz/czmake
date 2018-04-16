import sys
import os
from subprocess import check_call, CalledProcessError

def run():
    try:
        check_call(['czmake-' + sys.argv[1]] + sys.argv[2:])
    except CalledProcessError as cpe:
        sys.exit(cpe.returncode)
        pass

if __name__ == "__main__":
    run()