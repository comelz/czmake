import argparse
import json
import os
import sys
import logging
import platform
from multiprocessing import cpu_count
from os.path import dirname, abspath, join, exists, basename
from shutil import rmtree
from subprocess import check_call
from .utils import DirectoryContext, mkdir, str2bool, cmake_exe, parse_option, dump_option

logger = logging.getLogger(__name__)

def fork(*args, **kwargs):
    sys.stdout.write(' '.join(args[0]) + '\n')
    return check_call(*args, **kwargs)

def argv_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", action='store_true',
                        help="Calls the install target at the end of the build process")
    parser.add_argument("--package", action='store_true',
                        help="Run CPack at the end of the build process")
    parser.add_argument("-E", "--cmake-exe", help="use specified cmake executable", metavar='CMAKE_EXE', default=cmake_exe)
    parser.add_argument("-j", "--jobs", metavar="JOBS", type=int,
                        help="maximum number of concurrent jobs (only works if native build system has support for '-j N' command line parameter)")
    parser.add_argument("-T", "--cmake-target", nargs='*', help="build specified cmake target(s)")
    parser.add_argument("build_directory", help="directory in which the build will take place", metavar='BUILD_DIR')
    parser.add_argument("extra_args", nargs='*', help="extra arguments to pass to CMake or native build system")
    args = parser.parse_args()
    return args


def build(configuration):
    cfg = configuration
    env = os.environ
    if platform.system() != 'Windows' and 'MAKEFLAGS' not in os.environ:
        env['MAKEFLAGS'] = "-j%d" % cpu_count()
    extra_args = ['--']
    if not cfg['jobs'] is None:
        extra_args += ['-j%d' % cfg['jobs']]
    if cfg['extra_args']:
        extra_args += cfg['extra_args']
    if len(extra_args) == 1:
        extra_args = []
    if cfg['cmake_target'] and len(cfg['cmake_target']) > 0:
        for target in cfg['cmake_target']:
            build_cmd = [cfg['cmake_exe'], '--build', cfg['build_directory'], '--target', target] + extra_args
            fork(build_cmd, env=env)
    else:
        build_cmd = [cfg['cmake_exe'], '--build', cfg['build_directory']] + extra_args
        fork(build_cmd, env=env)


def run():
    logging.basicConfig(format='%(levelname)s: %(message)s')
    args = argv_parse()
    build(vars(args))

if __name__ == '__main__':
    run()
