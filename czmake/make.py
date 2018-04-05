#!/bin/env python3

from argparse import ArgumentParser
from .build import build, run, str2bool


def run():
    parser = ArgumentParser(description='Quick cmake build helper tool')
    parser.add_argument("-b", "--build-type", metavar="BUILD_TYPE",
                        help="Specify cmake build type")
    parser.add_argument("-C", "--clean-build", type=str2bool,
                        help="choose whether or not delete the build directory at the beginning of the build",
                        default=False, metavar='(true|false)')
    parser.add_argument("-t", "--toolchain-file", metavar="TOOLCHAIN_FILE",
                        help="Specify the cmake toolchain file")
    parser.add_argument("-d", "--build-directory", metavar="BUILD_DIR", default='.',
                        help="Specify the build directory")
    parser.add_argument("-e", "--extra-args", nargs="*", help="extra arguments to pass to CMake")
    parser.add_argument("-n", "--no-build", action='store_true',
                        help="Just run cmake without building anything")
    parser.add_argument("-g", "--launch-ccmake", action='store_true',
                        help="Run ccmake before building")
    parser.add_argument("-p", "--package", action='store_true',
                        help="Run CPack at the end of the build process")
    parser.add_argument("-i", "--install", action='store_true',
                        help="Calls the install target at the end of the build process")
    parser.add_argument("-o", "--cmake-options", metavar="CMAKE_OPTION", action='append',
                        help="Add CMake command line option (e.g. -o STATIC_QT5=ON => cmake -DSTATIC_QT5=ON) ...")
    parser.add_argument("-E", "--cmake-exe", help="use specified cmake executable", metavar='FILE', default='cmake')
    parser.add_argument("-G", "--generator", metavar="CMAKE_GENERATOR",
                        help="Specify CMake generator (e.g. 'CodeLite - Unix Makefiles')")
    parser.add_argument("cmake-targets", nargs='*', help="build specified cmake target(s)", metavar='CMAKE_TARGETS')
    parser.add_argument("-j", "--jobs", metavar="JOBS",
                        help="maximum number of concurrent jobs (works only if native build system has support for '-j N' command line parameter)")
    parser.add_argument("-c", "--ccache", action="store_true", help="Use ccache")
    parser.add_argument("-s", "--source-directory", metavar='SRC_DIR',
                        help="Directory where to the main CMakeLists.txt is located")

    optlist = parser.parse_args()
    configuration = {key.replace('_', '-'): value for key, value in optlist.__dict__.items() if value is not None and
                     key != 'toolchain_file' and
                     key != 'package' and
                     key != 'ccache' and
                     key != 'cmake_options'}
    options = []
    if optlist.cmake_options:
        for opt in optlist.cmake_options:
            options.append('-D%s' % (opt))
    configuration['options'] = options
    if optlist.toolchain_file:
        configuration['options'].append('-DCMAKE_TOOLCHAIN_FILE=%s' % optlist.toolchain_file)
    if optlist.build_type:
        configuration['options'].append('-DCMAKE_BUILD_TYPE=%s' % optlist.build_type)
    if optlist.ccache:
        configuration['options'].append('-DCMAKE_C_COMPILER_LAUNCHER=ccache')
        configuration['options'].append('-DCMAKE_CXX_COMPILER_LAUNCHER=ccache')
    if optlist.install:
        configuration['cmake-targets'] = ['install']
    if optlist.package:
        configuration['cmake-targets'] = ['package']
    if 'source-directory' not in configuration:
        configuration['source-directory'] = None
        configuration['build-directory'] = configuration['build-directory'] or '.'

    build(configuration)


if __name__ == "__main__":
    run()
