import os
import os.path
import subprocess
import argparse

cmake_exe = os.environ.get('CZMAKE_CMAKE', 'cmake')

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if not os.path.exists(path):
            raise e


def mkcd(path): mkdir(path) and pushd(path)


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1', 'on'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0', 'off'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


def strip(filepath, ts_filepath=None):
    if not ts_filepath:
        ts_filepath = filepath + '.strip_timestamp'
    touch(ts_filepath)
    subprocess.check_output(['strip', '-s', filepath])


def upx(filepath, ts_filepath=None):
    if not ts_filepath:
        ts_filepath = filepath + '.upx_timestamp'
    touch(ts_filepath)
    subprocess.check_output(['upx', '--best', filepath])


def _init():
    dir_stack = []

    def pushd(*args):
        dir_stack.append(os.getcwd())
        ndir = os.path.realpath(os.path.join(*args))
        os.chdir(ndir)

    def popd():
        odir = dir_stack.pop()
        os.chdir(odir)

    return pushd, popd


pushd, popd = _init()


class DirectoryContext():
    def __init__(self, dirpath):
        self.dirpath = dirpath

    def __enter__(self):
        pushd(self.dirpath)
        return self.dirpath

    def __exit__(self, *args):
        popd()
