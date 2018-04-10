#!/usr/bin/env python3

import argparse
import json
import sys
from os.path import join, exists
from shutil import rmtree
from urllib.parse import urlparse

from czmake.checkout import download, SCM
from czmake.cmake_cache import read_cache
from czmake.utils import mkcd, write_if_different


def argv_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source-dir", help="specify source directory", metavar='DIR')
    parser.add_argument("-b", "--build-dir", help="specify build directory", metavar='DIR')
    parser.add_argument("-r", "--repo-dir", help="specify directory to download dependencies", metavar='DIR')
    parser.add_argument("-c", "--cache-file", help="specify cmake cache file", metavar='CACHE_FILE')
    parser.add_argument("-C", "--clean", help="clean repository directory", action='store_true')
    args = parser.parse_args()
    return args


args = argv_parse()


class Node:
    def __init__(self):
        self.children = set()


class Module(Node):
    repodir = args.repo_dir

    def __init__(self, name=None, uri=None):
        super().__init__()
        self.name = name
        if uri:
            uri = urlparse(uri)
            self.scm = SCM.fromURI(uri)
        self.uri = uri
        self.cmake_options = {}
        self.dependencies = set()
        self.directory = join(Module.repodir, name) if name else args.source_dir
        self.condition = {}

    def __hash__(self):
        return self.name.__hash__()


def walkTree(root, callback):
    class StackElement:
        def __init__(self, node):
            self.node = node
            self.index = 0
            self.children = list(node.children)

    stack = [StackElement(root)]
    while len(stack) > 0:
        stack_element = stack[-1]
        if stack_element.index == len(stack_element.children):
            if callback.__code__.co_argcount == 1:
                callback(stack_element.node)
            if callback.__code__.co_argcount == 2:
                callback(stack_element.node, len(stack))
            stack.pop()
        else:
            child = stack_element.children[stack_element.index]
            stack.append(StackElement(child))
            stack_element.index += 1


def run():
    if args.clean:
        rmtree(Module.repodir)
    mkcd(Module.repodir)
    modules = {}

    cache_file = args.cache_file
    cache = (cache_file and exists(cache_file) and read_cache(open(cache_file, 'r')) or {})
    root = Module()
    node_stack = [root]
    while len(node_stack):
        parent_node = node_stack.pop()
        externals_file = join(parent_node.directory, 'externals.json')
        if exists(externals_file):
            try:
                conf = json.load(open(externals_file, 'r'))
                for module_name, module_object in conf["depends"].items():
                    if module_name in modules:
                        module = modules[module_name]
                    else:
                        module = Module(module_name, module_object['uri'])
                        download(module.scm, module.uri, module.directory)
                        modules[module_name] = module
                    if "options" in module_object:
                        for key, value in module_object['options'].items():
                            if key not in module.cmake_options:
                                module.cmake_options[key] = cache.get(key, value)
                    parent_node.children.add(module)
                    node_stack.append(module)
                if 'optdepends' in conf:
                    module = parent_node
                    for cmake_option, values in conf['optdepends'].items():
                        for depobj in values:
                            if ((cmake_option in module.cmake_options and module.cmake_options[cmake_option] == depobj['value']) or
                                        (cmake_option in cache and
                                        cache.get(cmake_option, depobj['value']) == depobj['value'])):
                                for depname, depobject in depobj['deps'].items():
                                    if depname in modules:
                                        additional_module = modules[depname]
                                    elif 'uri' in depobject:
                                        additional_module = Module(depname, depobject['uri'])
                                        download(additional_module.scm, additional_module.uri,
                                                 additional_module.directory)
                                        modules[depname] = additional_module
                                    else:
                                        raise ValueError("Cannot retrieve module '%s'" % depname)
                                    node = additional_module
                                    if 'options' in depobject:
                                        for key, value in depobject['options'].items():
                                            if key not in additional_module.cmake_options:
                                                additional_module.cmake_options[key] = value
                                    parent_node.children.add(node)
                                    node_stack.append(node)
                            else:
                                for depname, depobject in depobj['deps'].items():
                                    if depname in modules and 'options' in depobject:
                                        module = modules[depname]
                                        for key, value in depobject['options'].items():
                                            if key not in module.cmake_options:
                                                module.cmake_options[key] = None

            except json.JSONDecodeError:
                sys.stderr.write('Error parsing "%s"\n' % externals_file)
                raise

    def build_module_tree(node):
        if node:
            for child in node.children:
                node.dependencies.add(child)

    walkTree(root, build_module_tree)

    processed_modules = set()
    cmake_file = ''

    def processModule(module):
        nonlocal cmake_file
        if module.name and module not in processed_modules:
            for key, value in module.cmake_options.items():
                if value is None:
                    cmake_file += 'unset(%s CACHE)\n' % (key)
                    continue    
                elif isinstance(value, bool):
                    kind = "BOOL"
                    value = 'ON' if value else 'OFF'
                else:
                    kind = "STRING"
                cmake_file += 'set(%s %s CACHE %s "" FORCE)\n' % (key, value, kind)
            cmake_file += 'add_subdirectory(%s)\n' % module.name
            processed_modules.add(module)

    walkTree(root, processModule)
    write_if_different(join(Module.repodir, 'CMakeLists.txt'), cmake_file)


if __name__ == '__main__':
    run()
