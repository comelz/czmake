#!/usr/bin/env python3

from os import getcwd
from os.path import join, exists, abspath
from utils import pushd, popd, mkcd, mkdir, str2bool
from subprocess import check_call as run, check_output
from shutil import rmtree
from checkout import download, SCM
from urllib.parse import urlparse
import argparse

import json
import sys


def argv_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source-dir", help="specify source directory", metavar='DIR')
    parser.add_argument("-r", "--repo-dir", help="specify directory to download dependencies", metavar='DIR')
    parser.add_argument("-c", "--clean", help="clean repository directory", action='store_true')
    args = parser.parse_args()
    return args


args = argv_parse()

class Module:
    repodir = args.repo_dir

    def __init__(self, name=None, uri=None):
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

class Node:
    def __init__(self, obj=None):
        self.obj = obj
        self.children = set()


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


if args.clean:
    rmtree(Module.repodir)
source_dir = args.source_dir
mkcd(Module.repodir)
modules = {}

root = Node(Module())
node_stack = [root]
while len(node_stack):
    parent_node = node_stack.pop()
    externals_file = join(parent_node.obj.directory, 'externals.json')
    if exists(externals_file):
        try:
            conf = json.load(open(externals_file, 'r'))
            for module_name, module_object in conf["depends"].items():
                if module_name in modules:
                    node = Node(modules[module_name])
                else:
                    module = Module(module_name, module_object['uri'])
                    download(module.scm, module.uri, module.directory)
                    node = Node(module)
                    modules[module_name] = module
                if "options" in module_object:
                    for key, value in module_object['options'].items():
                        if key not in module.cmake_options:
                            module.cmake_options[key] = value
                parent_node.children.add(node)
                node_stack.append(node)
            if 'optdepends' in conf:
                module = parent_node.obj
                for cmake_option, values in conf['optdepends'].items():
                    for depobj in values:
                        if (cmake_option in module.cmake_options and
                                    module.cmake_options[cmake_option] == depobj['value']):
                            for depname, depobject in depobj['deps'].items():
                                if depname in modules:
                                    additional_module = modules[depname]
                                elif 'uri' in depobject:
                                    additional_module = Module(depname, depobject['uri'])
                                    download(additional_module.scm, additional_module.uri, additional_module.directory)
                                else:
                                    raise ValueError("Cannot retrieve module '%s'" % depname)
                                node = Node(additional_module)
                                if 'options' in depobject:
                                    for key, value in depobject['options'].items():
                                        if key not in additional_module.cmake_options:
                                            additional_module.cmake_options[key] = value
                                parent_node.children.add(node)
                                node_stack.append(node)
        except json.JSONDecodeError:
            sys.stderr.write('Error parsing "%s"\n' % external_file)
            raise


def build_module_tree(node):
    if node.obj:
        for child in node.children:
            node.obj.dependencies.add(child.obj)


walkTree(root, build_module_tree)

processed_modules = set()
cmake_file = open(join(Module.repodir, 'CMakeLists.txt'), 'w')


def processModule(node):
    module = node.obj
    if module.name and module not in processed_modules:
        for key, value in module.cmake_options.items():
            if isinstance(value, bool):
                kind = "BOOL"
                value = 'ON' if value else 'OFF'
            else:
                kind = "STRING"
            cmake_file.write('set(%s %s CACHE %s "")\n' % (key, value, kind))
        cmake_file.write('add_subdirectory(%s)\n' % module.name)
        processed_modules.add(module)


walkTree(root, processModule)
