from urllib.parse import urlparse
from os.path import exists, abspath, basename
from subprocess import check_output, check_call as run
from utils import pushd, popd
import sys


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


def download(scm, uri, destination):
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

        url = uri._replace(fragment='').geturl()
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
        ref = (uri.fragment and parse_fragment(uri.fragment).get('rev', 'HEAD')) or 'HEAD'
        url = uri._replace(fragment='').geturl()
        if exists(destination):
            print("Downloading '%s' from %s" % (name, url))
            run(['svn', 'update', '-r', ref, destination])
        else:
            run(['svn', 'checkout', '-r', ref, url, destination])


if __name__ == '__main__':
    uri = urlparse(sys.argv[1])
    scm = SCM(uri)
    destination = sys.argv[2]
    download(name, scm, uri, destination)
