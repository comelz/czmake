from time import sleep
from shutil import rmtree
from hashlib import md5
from urllib.parse import urlparse
from os import getcwd, unlink, symlink, listdir
from os.path import exists, abspath, basename, join, expanduser
from subprocess import check_output, call
from .utils import pushd, popd, DirectoryContext, parse_option, dump_option, mkdir, fork
import sys
import argparse
import json
import platform
import fcntl
import logging
import os

logger = logging.getLogger(__name__)
checkout_dir = expanduser('~/.czmake')
mkdir(checkout_dir)

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

    @staticmethod
    def detect(path='.'):
        retcode = call(['svn', 'info', path])
        if retcode == 0: return SCM.svn
        retcode = call(['git', 'status', path])
        if retcode == 0: return SCM.git


class FileLock:

    def __init__(self, filepath):
        self._filepath = filepath
    
    def __enter__(self):
        import errno
        self._fd = os.open(self._filepath, os.O_RDONLY)
        while True:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as e:
                if e.errno != errno.EAGAIN:
                    raise
                else:
                    sleep(0.3)

    def __exit__(self, *args):
        fcntl.flock(self._fd, fcntl.LOCK_UN)
        os.close(self._fd)

def repo_cleanup():
    with FileLock(checkout_dir):
        for entry in listdir(checkout_dir):
            sandbox_dir = join(checkout_dir, entry)
            refcount_file = join(sandbox_dir, '.czmake_refcount')
            existing_build_dirs = []
            rewrite = False
            with open(refcount_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if exists(line):
                        existing_build_dirs.append(line)
                    else:
                        rewrite = True
            if rewrite:
                if len(existing_build_dirs):
                    with open(refcount_file, 'w') as f:
                        for line in existing_build_dirs:
                            f.write(line)
                            f.write('\n')
                else:
                    local_edit = len(check_output(['svn', 'st', '-q', sandbox_dir]).decode('utf-8').split('\n')) > 1
                    if not local_edit:
                        rmtree(sandbox_dir)
                    else:
                        logger.warning('No build directory is using "%s" but, since it contains local modifications, it will not be garbage collected')


def download(uri, destination, scm=None, update=False):
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
                fork(['git', 'fetch', '--all', '-p'])
        else:
            print("Downloading '%s' from %s" % (name, url))
            fork(['git', 'clone', '--mirror', url, destination])
        pushd(destination)
        fork(['git', 'checkout', '--force', '--no-track', '-B', 'cmake_utils', ref])
        popd()
    elif scm == SCM.svn:
        fragment = (uri.fragment and parse_fragment(uri.fragment)) or {}
        rev = fragment.get('rev', None)
        branch = fragment.get('branch', None)
        tag = fragment.get('tag', None)
        url = uri._replace(fragment='')
        if (branch or tag) and url.path.endswith('trunk'):
            url = url._replace(path=url.path[:-5])
        if branch:
            url = url._replace(path=join(url.path, 'branches', branch))
        elif tag:
            url = url._replace(path=join(url.path, 'tags', tag))
        if rev:
            url = url._replace(path=url.path + '@' + rev)
        if platform.system() == 'Linux':
            with FileLock(checkout_dir):
                checkout_hash = md5(url.geturl().encode()).digest().hex()
                checkout_dest = join(checkout_dir, checkout_hash)
                if exists(checkout_dest):
                    if update:
                        fork(['svn', 'up', '-r', rev or 'HEAD', checkout_dest])
                else:
                    fork(['svn', 'checkout', url.geturl(), checkout_dest])
                exists(destination) and unlink(destination)
                symlink(checkout_dest, destination)
                with open(join(checkout_dest, '.czmake_refcount'), 'a') as f:
                    print(abspath(destination), file=f)
        elif exists(destination):
            if not update:
                return
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
                    fork(['svn', 'switch', url.geturl(), destination])
                else:
                    raise ValueError(
                        "Cannot switch URL of local checkout in '%s' because there are local modifications" % destination)
            
            print("Downloading '%s' from %s" % (name, url.geturl()))
            fork(['svn', 'update', '-r', ref, destination])
        else:
            fork(['svn', 'checkout', '-r', ref, url.geturl(), destination])

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
    parser.add_argument("-r", "--repo-dir", help="specify directory to download dependencies, defaults to ${BUILD_DIRECTORY}/czmake", metavar='REPO_DIR')
    parser.add_argument("-o", "--option", metavar="OPTION", action='append',
                        help="Set czmake option (e.g. -o STATIC_QT5=ON => cmake -DSTATIC_QT5=ON) ...")
    parser.add_argument("-C", "--clean", help="clean repository directory", action='store_true')
    args = parser.parse_args()
    solve_dependencies(generate_cmake=False, clean=args.clean, repo_dir=args.repo_dir, opts=manage_options(args), update=True)

if __name__ == '__main__':
    clone()
