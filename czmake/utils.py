# -*- coding: utf8 -*-
from builtins import object

import argparse
import hashlib
import os
import os.path
import subprocess
import sys

cmake_exe = os.environ.get('CZMAKE_CMAKE', 'cmake')
cache_file = os.path.join('czmake_cache.json')


if sys.version_info.major == 2:
    def items(dictionary):
        return dictionary.iteritems()
else:
    def items(dictionary):
        return dictionary.items()


def update_dict(original, updated):
    for key, value in items(updated):
        fixed_key = key.replace('-', '_')
        if fixed_key in original and isinstance(value, dict):
            update_dict(original[fixed_key], value)
        elif not fixed_key in original:
            original[fixed_key] = value
        elif fixed_key in original and value:
            original[fixed_key] = value


def fork(*args, **kwargs):
    sys.stdout.write(' '.join(args[0]) + '\n')
    return subprocess.check_call(*args, **kwargs)


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
        key, value = s[:colon], s[eq + 1:]
        try:
            value = str2bool(value)
        except argparse.ArgumentTypeError:
            pass
    else:
        key = s[:colon]
        ty = s[colon + 1:eq].lower()
        if ty == 'BOOL':
            value = str2bool(s[eq + 1])
        else:
            value = s[eq + 1]
    return key, value


def mkdir(path):
    """Make the directory or do nothing if it already exists.

    Equivalent to Py3-only `os.makedirs(path, exist_ok=True)`.
    """
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
        # if the file is not present, let's go ahead to write it now
        pass
    if md5.digest() != newdigest:
        open(filepath, 'w').write(content)


def mkcd(path):
    # Note: most likely this function is not used anymore.
    #       When we will be sure about it, we can remove it.
    mkdir(path) and pushd(path)


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


class DirectoryContext(object):
    def __init__(self, dirpath):
        self.dirpath = dirpath

    def __enter__(self):
        pushd(self.dirpath)
        return self.dirpath

    def __exit__(self, *args):
        popd()
