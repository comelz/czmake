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
from .utils import DirectoryContext, mkdir, str2bool, cmake_exe, parse_option, dump_option, update_dict, cache_file

logger = logging.getLogger(__name__)

def fork(*args, **kwargs):
    sys.stdout.write(' '.join(args[0]) + '\n')
    return check_call(*args, **kwargs)

def argv_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", type=str2bool, nargs='?', const=True, metavar='(true|false)',
                        help="Calls the install target at the end of the build process")
    parser.add_argument("--package", type=str2bool, nargs='?', const=True, metavar='(true|false)',
                        help="Run CPack at the end of the build process")
    parser.add_argument("-j", "--jobs", metavar="JOBS", type=int,
                        help="maximum number of concurrent jobs (only works if native build system has support for '-j N' command line parameter)")
    parser.add_argument("-T", "--cmake-target", nargs='*', help="build specified cmake target(s)")
    parser.add_argument("-b", "--build-directory", help="directory in which the build will take place", metavar='BUILD_DIR', default='.')
    parser.add_argument("extra_args", nargs='*', help="extra arguments to pass to CMake or native build system")
    args = parser.parse_args()
    return args


def build(configuration):
    cfile = join(configuration['build_directory'], cache_file)
    if exists(cfile):
        with open(cfile, 'r') as f:
            cfg = json.load(f)
    else:
        cfg = {}
    update_dict(cfg, configuration)

    env = os.environ
    if platform.system() != 'Windows' and 'MAKEFLAGS' not in os.environ:
        env['MAKEFLAGS'] = "-j%d" % cpu_count()
    extra_args = ['--']
    if cfg.get('jobs', None):
        extra_args += ['-j%d' % cfg['jobs']]
    if cfg.get('extra_args', None):
        extra_args += cfg['extra_args']
    if len(extra_args) == 1:
        extra_args = []
    if cfg.get('cmake_target', None) and len(cfg['cmake_target']) > 0:
        for target in cfg['cmake_target']:
            build_cmd = [cfg['cmake_exe'], '--build', cfg['build_directory'], '--target', target] + extra_args
            fork(build_cmd, env=env)
    else:
        build_cmd = [cfg.get('cmake_exe', cmake_exe), '--build', cfg['build_directory']] + extra_args
        fork(build_cmd, env=env)


def run():
    logging.basicConfig(format='%(levelname)s: %(message)s')
    cfg = vars(argv_parse())
    if isinstance(cfg['cmake_target'], str):
        cfg['cmake_target'] = set(cfg['cmake_target'])
    elif cfg['cmake_target']:
        cfg['cmake_target'] = set(cfg['cmake_target'])
    if cfg['package']:
        cfg['cmake_target'] = cfg.get('cmake_target', []) + ['package']
    elif cfg['package'] == False and cfg['cmake_target']:
        cfg['cmake_target'] = [target for target in cfg['cmake_target'] if target != 'package']
    if cfg['install']:
        cfg['cmake_target'] = cfg.get('cmake_target', []) + ['install']
    elif cfg['install'] == False and cfg['cmake_target']:
        cfg['cmake_target'] = [target for target in cfg['cmake_target'] if target != 'install']
    build(cfg)

if __name__ == '__main__':
    run()
