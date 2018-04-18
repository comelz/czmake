import os
import os.path
import subprocess
import argparse
import hashlib

cmake_exe = os.environ.get('CZMAKE_CMAKE', 'cmake')

def dump_option(key, value):
    if isinstance(value, bool):
        return '-D%s=%s' % (key, 'ON' if value else 'OFF')
    else:
        return '-D%s=%s' % (key, value)

def parse_option(s):
    eq = s.find('=')
    if eq < 0:
        raise ValueError('Unable to parse option: "%s"' % s)
    colon = s.find(':')
    if colon < 0:
        colon = eq
        key, value = s[:colon], s[eq+1:]
        try:
            value = str2bool(value)
        except argparse.ArgumentTypeError:
            pass
    else:
        key = s[:colon]
        ty = s[colon + 1:eq].lower()
        if ty == 'BOOL':
            value = str2bool(s[eq+1])
        else:
            value = s[eq+1]
    return key, value

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if not os.path.exists(path):
            raise e

def write_if_different(filepath, content, bufsize=256 * 256):
    newdigest = hashlib.md5(content.encode()).digest()
    md5 = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            while True:
                buffer = f.read(bufsize)
                md5.update(buffer)
                if len(buffer) < bufsize:
                    break
    except FileNotFoundError:
        pass
    if md5.digest() != newdigest:
        open(filepath, 'w').write(content)

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
