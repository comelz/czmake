import sys
from os import access, environ, pathsep, X_OK, listdir
from os.path import isfile, split, join
from shutil import which
from subprocess import check_call, CalledProcessError

def run():
    try:
        if len(sys.argv) > 1 and which('czmake-' + sys.argv[1]):
            check_call(['czmake-' + sys.argv[1]] + sys.argv[2:])
        else:
            def is_exe(fpath):
                return isfile(fpath) and access(fpath, X_OK)
            exes = {}
            for path in environ["PATH"].split(pathsep):
                try:
                    for entry in listdir(path):
                        if not entry.startswith('czmake-'):
                            continue
                        exe_file = join(path, entry)
                        if is_exe(exe_file) and not entry in exes:
                            exes[entry] = exe_file
                except FileNotFoundError:
                    pass
            print('\nAvailable commands:\n')
            for cmd in exes.keys():
                print('    ' + cmd.replace('czmake-', ''))
    except CalledProcessError as cpe:
        sys.exit(cpe.returncode)
        pass

if __name__ == "__main__":
    run()