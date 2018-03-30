#!/bin/env python3

import os
from argparse import ArgumentParser
from subprocess import run
from os.path import abspath, dirname, join
from .utils import popd, pushd, mkdir

def build(source_directory=None,
        build_directory=None,
        build_type=None, 
        toolchain_file=None, 
        package=False, 
        cmake_options=None, 
        generator=None, 
        no_build=None,
        launch_ccmake=None,
        cmake_targets=None,
        ccache=None,
        jobs=None,
        extra_args=None):
    if not build_type:
        build_type = 'Release'
    if source_directory:
        source_directory = abspath(source_directory)
    options = ['-DCMAKE_MODULE_PATH=%s' % join(dirname(__file__), 'cmake')]
    if build_type:
        options.append('-DCMAKE_BUILD_TYPE=%s' % (build_type))
    if toolchain_file:
        options.append('-DCMAKE_TOOLCHAIN_FILE=%s' % (toolchain_file))
    if generator:
       options.append('-G')
       options.append('%s' % (generator))
    if cmake_options:
        for opt in cmake_options:
            options.append('-D%s' % (opt))
    if extra_args:
        options += extra_args
    if ccache:
        options.append('-DCMAKE_C_COMPILER_LAUNCHER=ccache')
        options.append('-DCMAKE_CXX_COMPILER_LAUNCHER=ccache')            
    if build_directory:
        build_directory = os.path.abspath(build_directory)
        os.path.exists(build_directory) or os.makedirs(build_directory)
        pushd(build_directory)
    if source_directory:
        cmd = ['cmake'] + options + [source_directory]
        print(' '.join(cmd))
        run(cmd)
    if launch_ccmake:
        run(['ccmake', '.'])
    if no_build:
        return
    cmd = ['cmake', '--build', build_directory]

    if not cmake_targets:
        cmake_targets = []
    package and cmake_targets.append('package')
    if len(cmake_targets):
        for target in cmake_targets:
            cmd += ['--target', target]
    if jobs:
        cmd += ['--', '-j%d' % int(jobs)]
    print(' '.join(cmd))
    run(cmd)

if __name__ == '__main__':
    parser = ArgumentParser(description='Quick cmake build helper tool')
    parser.add_argument("-b", "--build-type", metavar="BUILD_TYPE",
                      help="Specify cmake build type")
    parser.add_argument("-t", "--toolchain-file", metavar="TOOLCHAIN_FILE",
                      help="Specify the cmake toolchain file")
    parser.add_argument("-d", "--build-directory", metavar="BUILD_DIR", default='.',
                      help="Specify the build directory")
    parser.add_argument("-n", "--no-build", action='store_true',
                      help="Just run cmake without building anything")
    parser.add_argument("-g", "--launch-ccmake", action='store_true',
                      help="Run ccmake before building")
    parser.add_argument("-p", "--package", action='store_true',
                      help="Run CPack at the end of the build process")
    parser.add_argument("-o", "--cmake-options", metavar="CMAKE_OPTION", action='append',
                      help="Add CMake command line option (e.g. -o STATIC_QT5=ON => cmake -DSTATIC_QT5=ON) ...")
    parser.add_argument("-G", "--generator", metavar="CMAKE_GENERATOR",
                      help="Specify CMake generator (e.g. 'CodeLite - Unix Makefiles') ")
    parser.add_argument("-T", "--cmake-targets", nargs='*', help="build specified cmake target(s)")
    parser.add_argument("-e", "--extra-args", nargs="*", help="extra arguments to pass to CMake")
    parser.add_argument("-j", "--jobs", metavar="CMAKE_OPTION", help="maximum number of concurrent jobs (works only if native build system has support for '-j N' command line parameter)")
    parser.add_argument("-c", "--ccache", action="store_true", help="Use ccache")
    parser.add_argument("-s", "--source-directory", metavar='SRC_DIR', help="Directory where to the main CMakeLists.txt is located")

    optlist = parser.parse_args()
    build(**optlist.__dict__)

