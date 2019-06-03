#!/bin/env python3
# -*- coding: utf8 -*-
from argparse import ArgumentParser, REMAINDER
from .build import build, parse_cmake_option
from .utils import cmake_exe, str2bool


def run():
    parser = ArgumentParser(description='Quick cmake build helper tool')
    parser.add_argument("-B", "--build-type", metavar="BUILD_TYPE",
                        help="Specify cmake build type")
    parser.add_argument("-C", "--clean-build", type=str2bool,
                        help="choose whether or not delete the build directory at the beginning of the build",
                        default=False, metavar='(true|false)')
    parser.add_argument("-t", "--toolchain-file", metavar="TOOLCHAIN_FILE",
                        help="Specify the cmake toolchain file")
    parser.add_argument("-b", "--build-directory", metavar="BUILD_DIR", default='.',
                        help="Specify the build directory")
    parser.add_argument('extra-args', nargs=REMAINDER)
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
    parser.add_argument("-E", "--cmake-exe", help="use specified cmake executable", metavar='CMAKE_EXE', default=cmake_exe)
    parser.add_argument("-G", "--generator", metavar="CMAKE_GENERATOR",
                        help="Specify CMake generator (e.g. 'CodeLite - Unix Makefiles')")
    parser.add_argument("-T", "--cmake-target", nargs='*', help="build specified cmake target(s)", metavar='CMAKE_TARGET')
    parser.add_argument("-j", "--jobs", metavar="JOBS",
                        help="maximum number of concurrent jobs (works only if native build system has support for '-j N' command line parameter)")
    parser.add_argument("-c", "--ccache", action="store_true", help="Use ccache")
    parser.add_argument("-l", "--lto", action="store_true", help="Enable link-time optimization support")
    parser.add_argument("-s", "--source-directory", metavar='SRC_DIR',
                        help="Directory where to the main CMakeLists.txt is located")

    optlist = parser.parse_args()
    configuration = {
        key.replace('_', '-'): value
        for key, value in optlist.__dict__.items()
        if value is not None
        and key != 'toolchain_file'
        and key != 'package'
        and key != 'ccache'
        and key != 'cmake_options'
    }
    options = {}
    if optlist.cmake_options:
        for opt in optlist.cmake_options:
            key, value = parse_cmake_option(opt)
            options[key] = value
    configuration['options'] = options
    if optlist.toolchain_file:
        configuration['options']['CMAKE_TOOLCHAIN_FILE'] = optlist.toolchain_file
    if optlist.build_type:
        configuration['options']['CMAKE_BUILD_TYPE'] = optlist.build_type
    if optlist.ccache:
        configuration['options']['CMAKE_C_COMPILER_LAUNCHER'] = 'ccache'
        configuration['options']['CMAKE_CXX_COMPILER_LAUNCHER'] = 'ccache'
    if optlist.lto:
        configuration['options']['CMAKE_INTERPROCEDURAL_OPTIMIZATION'] = True
    if optlist.install:
        configuration['cmake-target'] = ['install']
    if optlist.package:
        configuration['cmake-target'] = ['package']
    if 'source-directory' not in configuration:
        configuration['source-directory'] = None
        configuration['build-directory'] = configuration['build-directory'] or '.'

    build(configuration)


if __name__ == "__main__":
    run()
