from urllib.parse import urlparse
from os.path import exists, abspath, basename, join
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
        url = url.geturl()
        if exists(destination):
            out = check_output(['svn', 'st', '-q', destination]).decode('utf-8')
            local_edit = len(check_output(['svn', 'st', '-q', destination]).decode('utf-8').split('\n')) > 1
            prefix = 'URL: '
            for line in check_output(['svn', 'info', destination]).decode('utf-8').split('\n'):
                if line.startswith(prefix):
                    current_url = line[len(prefix):]
                    break
            else:
                raise ValueError("Cannot parse URL of local checkout in '%s'" % destination)
            if current_url != url:
                if not local_edit:
                    run(['svn', 'switch', url, destination])
                else:
                    raise ValueError("Cannot switch URL of local checkout in '%s' because there are local modifications" % destination)

            print("Downloading '%s' from %s" % (name, url))
            run(['svn', 'update', '-r', ref, destination])
        else:
            run(['svn', 'checkout', '-r', ref, url, destination])

if __name__ == '__main__':
    uri = urlparse(sys.argv[1])
    scm = SCM(uri)
    destination = sys.argv[2]
    download(name, scm, uri, destination)
