#!/usr/bin/env python3

from os import getcwd
from os.path import join, exists, abspath
from utils import pushd, popd, mkcd, mkdir, str2bool
from urllib.parse import urlparse
from subprocess import check_call as run, check_output
from shutil import rmtree
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


def parse_fragment(fragment):
    res = {}
    for equality in fragment.split():
        index = equality.find('=')
        key = equality[:index]
        value = equality[index + 1:]
        res[key] = value
    return res


class Module:
    repodir = args.repo_dir

    class SCM:
        git = object()
        svn = object()

    def __init__(self, name=None, uri=None):
        self.name = name

        if uri:
            uri = urlparse(uri)

            if uri.scheme.startswith('git'):
                self.scm = Module.SCM.git
            elif uri.scheme.startswith('svn'):
                self.scm = Module.SCM.svn
        self.uri = uri
        self.cmake_options = {}
        self.dependencies = set()
        self.directory = join(Module.repodir, name)

    def __hash__(self):
        return self.name.__hash__()

    def download(self):
        if exists(self.directory):
            return
        if self.scm == Module.SCM.git:
            ref = 'origin/HEAD'
            if self.uri.fragment:
                fragment = Module.parse_fragment(self.uri.fragment).get('rev', 'HEAD')
                if 'commit' in fragment:
                    ref = fragment['commit']
                elif 'tag' in fragment:
                    ref = fragment['tag']
                elif 'branch' in fragment:
                    ref = 'origin/%s' % fragment['branch']

            url = self.uri._replace(fragment='').geturl()
            if exists(self.directory):
                current_url = check_output(['git', 'config', '--get', 'remote.origin.url'])
                if url != current_url:
                    raise ValueError("Current git repository in '%s' is a clone of '%s' instead of '%s'" %
                                     (abspath(self.directory)), current_url, url)
                else:
                    run(['git', 'fetch', '--all', '-p'])

            else:
                print("Downloading '%s' from %s" % (self.name, url))
                run(['git', 'clone', '--mirror', url, self.directory])
            pushd(self.directory)
            run(['git', 'checkout', '--force', '--no-track', '-B', 'cmake_utils', ref])
            popd()
        elif self.scm == Module.SCM.svn:
            ref = (self.uri.fragment and parse_fragment(self.uri.fragment).get('rev', 'HEAD')) or 'HEAD'
            url = self.uri._replace(fragment='').geturl()
            if exists(self.directory):
                print("Downloading '%s' from %s" % (self.name, url))
                run(['svn', 'update', '-r', ref, self.directory])
            else:
                run(['svn', 'checkout', '-r', ref, url, self.directory])


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

root = Node()
node_stack = [root]
while len(node_stack):
    parent_node = node_stack.pop()
    module_dir = join(Module.repodir, parent_node.obj.name) if parent_node.obj else source_dir
    external_file = join(module_dir, 'externals.json')
    if exists(join(module_dir, 'externals.json')):
        try:
            conf = json.load(open(external_file, 'rb'))
            for module_name, module_object in conf["depends"].items():
                if module_name in modules:
                    node = Node(modules[module_name])
                else:
                    module = Module(module_name, module_object['uri'])
                    module.download()
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
                                    additional_module.download()
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
    if module and module not in processed_modules:
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
