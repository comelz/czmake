import os, json, argparse, sys
from multiprocessing import cpu_count
from shutil import rmtree
from subprocess import check_call


def run(*args, **kwargs):
    print(' '.join(args[0]))
    return check_call(*args, **kwargs)


def _init():
    dir_stack = []

    def pushd(ndir):
        dir_stack.append(os.getcwd())
        ndir = os.path.realpath(ndir)
        os.chdir(ndir)

    def popd():
        odir = dir_stack.pop()
        os.chdir(odir)

    return pushd, popd


pushd, popd = _init()


def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if not os.path.exists(path):
            raise e


def mkcd(path): mkdir(path) and pushd(path)


def update_dict(original, updated):
    for key, value in updated.items():
        if key in original and isinstance(value, dict):
            update_dict(original[key], value)
        else:
            original[key] = value

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1', 'on'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0', 'off'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def argv_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o' '--options', help='pass the argument to cmake prepended with -D', action='append')
    parser.add_argument("-G", "--generator", help="use specified cmake generator")
    parser.add_argument("-e", "--cmake-exe", help="use specified cmake executable", default='cmake')
    parser.add_argument("-t", "--target", nargs='*', help="build specified cmake target(s)")
    parser.add_argument("-c", "--configuration-file",
                        help="load build configuration from FILE, default is 'build.json'")
    parser.add_argument("-C", "--clean-build", type=str2bool, help="choose whether or not delete the build directory at the beginning of the build", default=None)
    parser.add_argument("-l", "--list", help="list build configurations", action='store_true')
    parser.add_argument("-p", "--print", help="show build configuration", action='store_true')
    parser.add_argument("-s", "--source-directory", help="directory where the main CMakeLists.txt file is located")
    parser.add_argument("-b", "--build-directory", help="directory in which the build will take place")
    parser.add_argument("configuration", type=str, nargs='*', help="name of the build configuration to use")
    args = parser.parse_args()
    return args


_source_directory = None
_build_directory = None
_project_directory = os.path.dirname(os.path.realpath(sys.argv[0]))


def source_directory(): return _source_directory


def build_directory(): return _build_directory


def project_directory(): return _project_directory


def build(default_configuration=None):
    args = argv_parse()
    if not args.configuration_file:
        args.configuration_file = os.path.join(project_directory(), 'build.json')
    build_cfg = json.load(open(args.configuration_file, 'rb'))
    if args.list:
        for cfg in sorted(build_cfg['configurations'].keys()):
            print cfg
        sys.exit(0)

    if not args.configuration:
        args.configuration = default_configuration or build_cfg['default']
    if isinstance(args.configuration, unicode):
        args.configuration = [args.configuration]
    configuration_list = []
    configuration_set = set()
    for configuration in args.configuration:
        if configuration not in build_cfg['configurations']:
            raise KeyError('Configuration "%s" does not exist in configuration provided by "%s"' %
                           (args.configuration, args.configuration_file))
        inheritance_list = [configuration]
        inheritance_set = set(inheritance_list)
        while True:
            cfg_key = inheritance_list[-1]
            parent = build_cfg['configurations'][cfg_key].get('inherits', None)
            if parent:
                if parent in configuration_set:
                    raise ValueError('Inheritance loop detected with build configuration "%s"' % parent)
                inheritance_list.append(parent)
                inheritance_set.add(parent)
            else:
                break
        for conf in reversed(inheritance_list):
            if conf not in configuration_set:
                configuration_set.add(parent)
                configuration_list.append(conf)

    bdirname = 'build-%s' % os.path.basename(project_directory())
    for conf in args.configuration:
        bdirname += '-' + conf

    cfg = {
        'build-directory': bdirname,
        'clean-build': False,
        'source-directory': 'src',
        'build-command': 'make',
        'cmake-target': 'all'
    }
    for conf in configuration_list:
        update_dict(cfg, build_cfg['configurations'][conf])

    if args.clean_build is not None:
        cfg['clean-build'] = args.clean_build
    if args.build_directory:
        cfg['build-directory'] = args.build_directory
    if args.source_directory:
        cfg['source-directory'] = args.source_directory
    if args.generator:
        cfg['generator'] = args.generator
    if args.target:
        cfg['cmake-target'] = args.target
    if (isinstance(cfg['cmake-target'], unicode) or
            isinstance(cfg['cmake-target'], str)):
        cfg['cmake-target'] = [cfg['cmake-target']]

    if args.o__options:
        for option in args.o__options:
            equal_char = option.find('=')
            key, value = option[:equal_char], option[equal_char + 1:]
            cfg['options'][key] = value
    global _build_directory, _source_directory
    _build_directory = cfg['build-directory']
    if cfg['clean-build']:
        os.path.exists(build_directory()) and rmtree(build_directory())
    cfg['source-directory'] = os.path.abspath(os.path.join(project_directory(), cfg['source-directory']))
    _source_directory = cfg['source-directory']

    if getattr(args, 'print'):
        print cfg
        sys.exit(0)
    mkdir(build_directory())
    pushd(build_directory())
    cmd = [args.cmake_exe]

    if 'generator' in cfg:
        cmd += ['-G', '%s' % (cfg['generator'])]
    for key, value in cfg["options"].items():
        cmd.append('-D%s=%s' % (key, value))
    cmd.append(cfg['source-directory'])

    run(cmd)
    env = os.environ
    if 'MAKEFLAGS' not in os.environ:
        env['MAKEFLAGS'] = "-j%d" % cpu_count()
    cmd = [cfg['build-command']] + cfg['cmake-target']
    run(cmd, env=env)
    popd()
    return args.configuration, cfg
