import argparse
import json
import os
import sys
import logging
import platform
from multiprocessing import cpu_count
from os.path import dirname, abspath, join, exists, basename
from shutil import rmtree
from .utils import DirectoryContext, mkdir, str2bool, cmake_exe, parse_option, dump_option, fork, update_dict, \
    cache_file
from .build import build

logger = logging.getLogger(__name__)


def argv_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--options', help='pass the argument to cmake prepended with -D', action='append',
                        metavar='KEY=VALUE')
    parser.add_argument("-B", "--build-type", metavar="BUILD_TYPE",
                        help="Specify cmake build type")
    parser.add_argument("-t", "--toolchain-file", metavar="TOOLCHAIN_FILE",
                        help="Specify the cmake toolchain file")
    parser.add_argument("--install", type=str2bool, nargs='?', const=True, metavar='(true|false)',
                        help="Calls the install target at the end of the build process")
    parser.add_argument("--package", type=str2bool, nargs='?', const=True, metavar='(true|false)',
                        help="Run CPack at the end of the build process")
    parser.add_argument("-g", "--launch-ccmake", action='store_true',
                        help="Run ccmake before building")
    parser.add_argument("-E", "--cmake-exe", help="use specified cmake executable", metavar='CMAKE_EXE')
    parser.add_argument("-G", "--generator", metavar="CMAKE_GENERATOR",
                        help="Specify CMake generator (e.g. 'CodeLite - Unix Makefiles')")
    parser.add_argument("-j", "--jobs", metavar="JOBS", type=int,
                        help="maximum number of concurrent jobs (only works if native build system has support for '-j N' command line parameter)")
    parser.add_argument("-T", "--cmake-target", nargs='*', help="build specified cmake target(s)")
    parser.add_argument("-f", "--configuration-file", default=join(os.getcwd(), 'build.czmake'),
                        help="load build configuration from CONFIGURATION_FILE, default is 'czmake_build.json'",
                        metavar='CONFIGURATION_FILE')
    parser.add_argument("-C", "--clean", type=str2bool, nargs='?', const=True,
                        help="choose whether or not delete the build directory at the beginning of the build",
                        metavar='(true|false)')
    parser.add_argument("--lto", type=str2bool, nargs='?', const=True, metavar='(true|false)',
                        help="Enable link-time optimization support")
    parser.add_argument("-l", "--list", help="list build configurations", action='store_true')
    parser.add_argument("--show", help="show build configuration", action='store_true')
    parser.add_argument("-b", "--build-directory", help="directory in which the build will take place", metavar='DIR')
    parser.add_argument("-p", "--project-directory",
                        help="root directory of the project (defaults to the directory of the build configuration file)")
    parser.add_argument("-s", "--source-directory", help="directory where the main CMakeLists.txt file is located",
                        metavar='DIR')
    parser.add_argument("--build", action='store_true', help="Start the build process after configuration is finished")
    parser.add_argument("-c", "--configuration-name", nargs='*', help="name of the build configuration to use")
    parser.add_argument("--ccache", type=str2bool, nargs='?', const=True, metavar='(true|false)', help="Use ccache")
    parser.add_argument("extra_args", nargs='*', help="extra arguments to pass to CMake or native build system")
    try: 
        import quark
        parser.add_argument("-u", "--update", help="update dependencies using quark", action="store_true",
                        metavar='DIR')
    except ImportError:
        pass
    args = parser.parse_args()
    return args


def parse_cfg(default_configuration=None):
    args = argv_parse()
    project_directory = args.project_directory or dirname(abspath(args.configuration_file)) if exists(
        args.configuration_file) else abspath('.')
    bdirname = 'build-%s' % basename(project_directory)
    configuration_list = []
    try:
        build_cfg = json.load(open(args.configuration_file, 'r'))
        if args.list:
            for cfg in sorted(build_cfg['configurations'].keys()):
                print(cfg)
            sys.exit(0)

        if not args.configuration_name:
            args.configuration_name = default_configuration or build_cfg['default']
        if isinstance(args.configuration_name, str):
            args.configuration_name = [args.configuration_name]
        configuration_set = set()
        for configuration in args.configuration_name:
            if configuration not in build_cfg['configurations']:
                raise KeyError('Configuration "%s" does not exist in configuration provided by "%s"' %
                               (args.configuration_name, args.configuration_file))
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
        for conf in args.configuration_name:
            bdirname += '-' + conf
    except FileNotFoundError as err:
        if args.configuration_name:
            raise err
        else:
            build_cfg = {}
            logger.warning('Build configuration file "%s" not found' % join(args.configuration_file))

    cfg = {
        'source_directory': '.',
        'build_directory': bdirname,
        'clean': False,
        'cmake_exe': cmake_exe,
        'cmake_target': None,
        'options': {
        },
    }
    with DirectoryContext(project_directory):
        if 'source_directory' in build_cfg:
            build_cfg['source_directory'] = abspath(build_cfg['source_directory'])
        if 'build_directory' in build_cfg:
            build_cfg['build_directory'] = abspath(build_cfg['build_directory'])

    for conf in configuration_list:
        update_dict(cfg, build_cfg['configurations'][conf])

    with DirectoryContext(project_directory):
        cfg['source_directory'] = abspath(cfg['source_directory'])
        cfg['build_directory'] = abspath(cfg['build_directory'])

    if args.toolchain_file:
        cfg['options']['CMAKE_TOOLCHAIN_FILE'] = args.toolchain_file
    if args.build_type:
        cfg['options']['CMAKE_BUILD_TYPE'] = args.build_type
    if args.ccache is not None:
        cfg['options']['CMAKE_C_COMPILER_LAUNCHER'] = 'ccache'
        cfg['options']['CMAKE_CXX_COMPILER_LAUNCHER'] = 'ccache'
    if args.lto is not None:
        cfg['options']['CMAKE_INTERPROCEDURAL_OPTIMIZATION'] = True
    if args.clean is not None:
        cfg['clean'] = args.clean
    if args.build_directory:
        cfg['build_directory'] = args.build_directory
    if args.source_directory:
        cfg['source_directory'] = args.source_directory
    if args.generator:
        cfg['generator'] = args.generator
    if args.cmake_exe:
        cfg['cmake_exe'] = args.cmake_exe
    if not args.cmake_target is None:
        cfg['cmake_target'] = args.cmake_target
    if isinstance(cfg['cmake_target'], str):
        cfg['cmake_target'] = [cfg['cmake_target']]
    if args.package:
        cfg['cmake_target'] = cfg.get('cmake_target', []) + ['package']
    elif args.package == False and cfg['cmake_target']:
        cfg['cmake_target'] = [target for target in cfg['cmake_target'] if target != 'package']
    if args.install:
        cfg['cmake_target'] = cfg.get('cmake_target', []) + ['install']
    elif args.install == False and cfg['cmake_target']:
        cfg['cmake_target'] = [target for target in cfg['cmake_target'] if target != 'install']
    cfg['extra_args'] = args.extra_args
    cfg['jobs'] = args.jobs
    cfg['build'] = args.build
    cfg['launch_ccmake'] = args.launch_ccmake

    if args.options:
        for option in args.options:
            key, value = parse_option(option)
            cfg['options'][key] = value
    cfg['project_directory'] = project_directory
    if args.show:
        print(json.dumps(cfg, indent=4))
        sys.exit(0)
    else:
        args_dict = vars(args)
        return args.configuration_name, cfg, {'update' : args_dict.get('update', False)}


def configure(configuration, update=False):
    if update:
        import quark
        quark.checkout.resolve_dependencies(configuration['source_directory'], options=configuration['options'])
    except ImportError:
        pass
    cfg = configuration
    env = os.environ
    if platform.system() != 'Windows' and 'MAKEFLAGS' not in os.environ:
        env['MAKEFLAGS'] = "-j%d" % cpu_count()
    if cfg['clean']:
        exists(cfg['build_directory']) and rmtree(cfg['build_directory'])
    mkdir(cfg['build_directory'])
    cmd = [cfg['cmake_exe'], '-DCMAKE_MODULE_PATH:PATH=%s' % join(dirname(__file__), 'cmake')]
    if 'generator' in cfg:
        cmd += ['-G', '%s' % (cfg['generator'])]
    for key, value in cfg["options"].items():
        cmd.append(dump_option(key, value))
    if cfg['build'] and 'extra_args' in cfg:
        cmd += cfg['extra_args']
    cfg['source_directory'] = abspath(cfg['source_directory'])
    cmd.append(cfg['source_directory'])

    with DirectoryContext(cfg['build_directory']):
        fork(cmd)
        if cfg.get('launch_ccmake', False):
            fork(['ccmake', '.'])


def run():
    logging.basicConfig(format='%(levelname)s: %(message)s')
    name, cfg, kwargs = parse_cfg()
    configure(cfg, **kwargs)
    if cfg.get('build', False):
        build(cfg)
    if cfg['build']:
        cfg['extra_args'] = None
    with DirectoryContext(cfg['build_directory']):
        del cfg['build']
        del cfg['build_directory']
        with open(cache_file, 'w') as f:
            json.dump(cfg, f)


if __name__ == '__main__':
    run()
