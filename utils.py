import os.path
import subprocess


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