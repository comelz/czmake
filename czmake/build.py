import argparse
import json
import os
import sys
from multiprocessing import cpu_count
from os.path import dirname, abspath, join, exists, basename
from shutil import rmtree
from subprocess import check_call
from .utils import DirectoryContext, mkdir, str2bool, cmake_exe

def run(*args, **kwargs):
    sys.stdout.write(' '.join(args[0]) + '\n')
    return check_call(*args, **kwargs)

def update_dict(original, updated):
    for key, value in updated.items():
        if key in original and isinstance(value, dict):
            update_dict(original[key], value)
        else:
            original[key] = value

def parse_cmake_option(s):
    index = s.index('=')
    if index < 0:
        raise ValueError('Unable to parse cmake property: "%s"' % s)
    else:
        return s[:index], s[index+1:]

def dump_cmake_option(key, value):
    if isinstance(value, bool):
        return '-D%s=%s' % (key, 'ON' if value else 'OFF')
    else:
        return '-D%s=%s' % (key, value)

def argv_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--options', help='pass the argument to cmake prepended with -D', action='append',
                        metavar='KEY=VALUE')
    parser.add_argument("-B", "--build-type", metavar="BUILD_TYPE",
                        help="Specify cmake build type")
    parser.add_argument("-t", "--toolchain-file", metavar="TOOLCHAIN_FILE",
                        help="Specify the cmake toolchain file")
    parser.add_argument("-i", "--install", action='store_true',
                        help="Calls the install target at the end of the build process")
    parser.add_argument("-p", "--package", action='store_true',
                        help="Run CPack at the end of the build process")
    parser.add_argument("-g", "--launch-ccmake", action='store_true',
                        help="Run ccmake before building")
    parser.add_argument("-X", "--cmake-exe", help="use specified cmake executable", metavar='CMAKE_EXE')
    parser.add_argument("-G", "--generator", metavar="CMAKE_GENERATOR",
                        help="Specify CMake generator (e.g. 'CodeLite - Unix Makefiles')")
    parser.add_argument("-E", "--build-extra-args", nargs="*", help="extra arguments to pass to native build system")
    parser.add_argument("-e", "--extra-args", nargs="*", help="extra arguments to pass to CMake")
    parser.add_argument("-j", "--jobs", metavar="JOBS",
                        help="maximum number of concurrent jobs (only works if native build system has support for '-j N' command line parameter)")
    parser.add_argument("-T", "--cmake-target", nargs='*', help="build specified cmake target(s)")
    parser.add_argument("-c", "--conf",
                        help="load build configuration from CONFIGURATION_FILE, default is 'build.json'", metavar='CONFIGURATION_FILE')
    parser.add_argument("-C", "--clean-build", type=str2bool,
                        help="choose whether or not delete the build directory at the beginning of the build",
                        default=None, metavar='(true|false)')
    parser.add_argument("-l", "--lto", action="store_true", help="Enable link-time optimization support")
    parser.add_argument("-L", "--list", help="list build configurations", action='store_true')
    parser.add_argument("-P", "--print", help="show build configuration", action='store_true')
    parser.add_argument("-s", "--source-directory", help="directory where the main CMakeLists.txt file is located",
                        metavar='DIR')
    parser.add_argument("-b", "--build-directory", help="directory in which the build will take place", metavar='DIR')
    parser.add_argument("-n", "--no-build", action='store_true', help="Just run cmake without building anything")
    parser.add_argument("configuration", type=str, nargs='*', help="name of the build configuration to use")
    args = parser.parse_args()
    return args


def parse_cfg(default_configuration=None):
    args = argv_parse()
    if not args.conf:
        args.conf = join(os.getcwd(), 'build.json')
    build_cfg = json.load(open(args.conf, 'r'))
    if args.list:
        for cfg in sorted(build_cfg['configurations'].keys()):
            print(cfg)
        sys.exit(0)
    project_directory = dirname(abspath(args.conf))
    if not args.configuration:
        args.configuration = default_configuration or build_cfg['default']
    if isinstance(args.configuration, str):
        args.configuration = [args.configuration]
    configuration_list = []
    configuration_set = set()
    for configuration in args.configuration:
        if configuration not in build_cfg['configurations']:
            raise KeyError('Configuration "%s" does not exist in configuration provided by "%s"' %
                           (args.configuration, args.conf))
        inheritance_list = [configuration]
        inheritance_set = set(inheritance_list)
        configuration_inheritance_set = set()
        while True:
            cfg_key = inheritance_list[-1]
            parent = build_cfg['configurations'][cfg_key].get('inherits', None)
            if parent:
                if parent in configuration_inheritance_set:
                    raise ValueError('Inheritance loop detected with build configuration "%s"' % parent)
                else:
                    configuration_inheritance_set.add(parent)
                inheritance_list.append(parent)
                inheritance_set.add(parent)
            else:
                break
        for conf in reversed(inheritance_list):
            if conf not in configuration_set:
                configuration_set.add(conf)
                configuration_list.append(conf)
    bdirname = 'build-%s' % basename(project_directory)
    for conf in args.configuration:
        bdirname += '-' + conf

    cfg = {
        'build-directory': bdirname,
        'clean-build': False,
        'source-directory': 'src',
        'build-command': 'make',
        'cmake-exe': cmake_exe,
        'cmake-target': 'all',
        'options': {

        }
    }
    for conf in configuration_list:
        update_dict(cfg, build_cfg['configurations'][conf])

    if args.toolchain_file:
        cfg['options']['CMAKE_TOOLCHAIN_FILE'] = args.toolchain_file
    if args.build_type:
        cfg['options']['CMAKE_BUILD_TYPE'] = args.build_type
    if args.clean_build is not None:
        cfg['clean-build'] = args.clean_build
    if args.build_directory:
        cfg['build-directory'] = args.build_directory
    if args.source_directory:
        cfg['source-directory'] = args.source_directory
    if args.generator:
        cfg['generator'] = args.generator
    if args.cmake_exe:
        cfg['cmake-exe'] = args.cmake_exe
    if args.extra_args:
        cfg['extra-args'] = args.extra_args
    if args.cmake_target:
        cfg['cmake-target'] = args.cmake_target
    if isinstance(cfg['cmake-target'], str):
        cfg['cmake-target'] = [cfg['cmake-target']]
    if args.package:
        cfg['cmake-target'].append('package')
    if args.install:
        cfg['cmake-target'].append('install')
    if args.lto:
        cfg['options']['CMAKE_INTERPROCEDURAL_OPTIMIZATION'] = True
    if args.options:
        for option in args.options:
            key, value = parse_cmake_option(option)
            cfg['options'][key] = value
    cfg['source-directory'] = abspath(join(project_directory, cfg['source-directory']))
    cfg['project-directory'] = project_directory

    if args.print:
        print(cfg)
        sys.exit(0)
    else:
        return args.configuration, cfg


def build(configuration):
    cfg = configuration
    env = os.environ
    if 'MAKEFLAGS' not in os.environ:
        env['MAKEFLAGS'] = "-j%d" % cpu_count()

    if cfg['source-directory']:
        if cfg['clean-build']:
            exists(cfg['build-directory']) and rmtree(cfg['build-directory'])
        mkdir(cfg['build-directory'])
        cmd = [cfg['cmake-exe'], '-DCMAKE_MODULE_PATH=%s' % join(dirname(__file__), 'cmake')]
        if 'generator' in cfg:
            cmd += ['-G', '%s' % (cfg['generator'])]
        for key, value in cfg["options"].items():
            cmd.append(dump_cmake_option(key, value))
        if 'extra-args' in cfg:
            cmd += cfg['extra-args']
        cmd.append(abspath(cfg['source-directory']))

        with DirectoryContext(cfg['build-directory']):
            run(cmd)
            if cfg.get('launch-ccmake', False):
                run(['ccmake', '.'])
    if not cfg.get('no-build', False):
        extra_args = ['--']
        if 'jobs' in cfg:
            extra_args += ['-j%d' % int(cfg['jobs'])]
        if 'build-extra-args' in cfg:
            extra_args += cfg['build-extra-args']
        if len(extra_args) == 1:
            extra_args = []
        if 'cmake-target' in cfg and len(cfg['cmake-target']) > 0:
            for target in cfg['cmake-target']:
                build_cmd = [cfg['cmake-exe'], '--build', cfg['build-directory'], '--target', target] + extra_args
                run(build_cmd, env=env)
        else:
            build_cmd = [cfg['cmake-exe'], '--build', cfg['build-directory']] + extra_args
            run(build_cmd, env=env)

if __name__ == '__main__':
    name, cfg = parse_cfg()
    build(cfg)
