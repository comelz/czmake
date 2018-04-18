from urllib.parse import urlparse
from os import getcwd
from os.path import exists, abspath, basename, join
from subprocess import check_output, check_call as run
from .utils import pushd, popd, DirectoryContext, parse_option, dump_option
import sys
import argparse
import json



class SCM:
    git = object()
    svn = object()

    @staticmethod
    def fromURI(uri):
        if uri.scheme.startswith('git'):
            return SCM.git
        elif uri.scheme.startswith('svn') or uri.path.startswith('^/'):
            return SCM.svn
        else:
            raise ValueError("Unrecognized SCM for url '%s'", uri.geturl())


def download(uri, destination, scm=None):
    if not scm:
        scm = SCM.fromURI(uri)
    name = basename(destination)

    def parse_fragment(fragment):
        res = {}
        for equality in fragment.split():
            index = equality.find('=')
            key = equality[:index]
            value = equality[index + 1:]
            res[key] = value
        return res

    if scm == SCM.git:
        ref = 'origin/HEAD'
        if uri.fragment:
            fragment = parse_fragment(uri.fragment).get('rev', 'HEAD')
            if 'commit' in fragment:
                ref = fragment['commit']
            elif 'tag' in fragment:
                ref = fragment['tag']
            elif 'branch' in fragment:
                ref = 'origin/%s' % fragment['branch']
        scheme = uri.scheme
        plus = scheme.find('+')
        if plus > 0:
            protocol = scheme[plus+1:]
            if protocol == 'https':
                scheme = 'https'
            elif protocol == 'http':
                scheme = 'http'
        url = uri._replace(fragment='', scheme=scheme).geturl()
        if exists(destination):
            current_url = check_output(['git', 'config', '--get', 'remote.origin.url'])
            if url != current_url:
                raise ValueError("Current git repository in '%s' is a clone of '%s' instead of '%s'" %
                                 (abspath(destination)), current_url, url)
            else:
                run(['git', 'fetch', '--all', '-p'])
        else:
            print("Downloading '%s' from %s" % (name, url))
            run(['git', 'clone', '--mirror', url, destination])
        pushd(destination)
        run(['git', 'checkout', '--force', '--no-track', '-B', 'cmake_utils', ref])
        popd()
    elif scm == SCM.svn:
        fragment = (uri.fragment and parse_fragment(uri.fragment)) or {}
        ref = fragment.get('rev', 'HEAD')
        branch = fragment.get('branch', None)
        tag = fragment.get('tag', None)
        url = uri._replace(fragment='')
        if (branch or tag) and url.path.endswith('trunk'):
            url = url._replace(url.path[:-5])
        if branch:
            url = url._replace(join(url.path, 'branches', branch))
        elif tag:
            url = url._replace(join(url.path, 'tags', tag))
        if exists(destination):
            local_edit = len(check_output(['svn', 'st', '-q', destination]).decode('utf-8').split('\n')) > 1
            if url.path.startswith('^'):
                prefix = 'Relative URL: '
            else:
                prefix = 'URL: '
            for line in check_output(['svn', 'info', destination]).decode('utf-8').split('\n'):
                if line.startswith(prefix):
                    current_url = urlparse(line[len(prefix):])
                    break
            else:
                raise ValueError("Cannot parse URL of local checkout in '%s'" % destination)
            if current_url != url:
                if not local_edit:
                    run(['svn', 'switch', url.geturl(), destination])
                else:
                    raise ValueError(
                        "Cannot switch URL of local checkout in '%s' because there are local modifications" % destination)

            print("Downloading '%s' from %s" % (name, url.geturl()))
            run(['svn', 'update', '-r', ref, destination])
        else:
            run(['svn', 'checkout', '-r', ref, url.geturl(), destination])

from czmake.dependency_solver import solve_dependencies

def manage_options(args):
    option_file = 'czmake_opts.json'
    options = exists(option_file) and json.load(open(option_file, 'w')) or {}
    if args.option:
        edit = False
        for option in args.option:
            key, value = parse_option(option)
            if options.get(key, None) != value:
                options[key] = value
                edit = True
        if edit:
            json.dump(options, open(option_file, 'w'), indent=4)
    return options

def clone():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--repo-dir", help="specify directory to download dependencies", metavar='REPO_DIR')
    parser.add_argument("-o", "--option", metavar="OPTION", action='append',
                        help="Set czmake option (e.g. -o STATIC_QT5=ON => cmake -DSTATIC_QT5=ON) ...")
    parser.add_argument("uri", help="the repository URI", metavar='URI')
    parser.add_argument("destination", nargs='?', help="checkout directory", metavar='DIR')
    args = parser.parse_args()   
    uri = urlparse(args.uri)
    destination = args.destination or basename(uri.path)
    download(uri, destination)
    with DirectoryContext(destination):
        options = manage_options(args)
        solve_dependencies(generate_cmake=False, repo_dir=args.repo_dir, opts=options)

def update():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source-dir", 
        help="specify source directory where the main 'czmake_deps.json' is located, defaults to current directory", 
        default=getcwd(), metavar='SOURCE_DIR')
    parser.add_argument("-r", "--repo-dir", help="specify directory to download dependencies, defaults to ${SOURCE_DIR}/lib", metavar='REPO_DIR')
    parser.add_argument("-o", "--option", metavar="OPTION", action='append',
                        help="Set czmake option (e.g. -o STATIC_QT5=ON => cmake -DSTATIC_QT5=ON) ...")
    parser.add_argument("-C", "--clean", help="clean repository directory", action='store_true')
    args = parser.parse_args()
    solve_dependencies(generate_cmake=False, clean=args.clean, repo_dir=args.repo_dir, opts=manage_options(args))

if __name__ == '__main__':
    clone()
