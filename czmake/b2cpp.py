#!/usr/bin/env python3

import argparse
import tempfile
from os.path import splitext, basename, join, dirname, realpath
from subprocess import Popen, PIPE

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert binary files to c++ source files for easy embed')
    parser.add_argument('-o', '--output-name', metavar='OUTPUT_FILE', dest='outfile', default='PKGBUILD', type=str,
                        required=True,
                        help='Name of the output files (this script will create two files with '
                             'this name apending the .cpp and .h extensions)')
    parser.add_argument('-n', '--namespace', metavar='NAMESPACE', dest='namespace', type=str,
                        required=False, help='')
    parser.add_argument('-e', '--encrypt', dest='encrypt', action='store_true')
    parser.add_argument('fvname', nargs='+')
    args = parser.parse_args()
    outpath, file_extension = splitext(args.outfile)
    fname = basename(outpath)
    outfile = open(outpath + ('.cpp' if args.namespace else '.c'), 'wb')

    def write(txt):
        outfile.write(txt.encode('utf-8'))

    write(('#include "%s"\n' % (fname + '.h')))
    if args.namespace:
        write('namespace %s {\n' % (args.namespace))

    if type(args.fvname) != list:
        args.fvname = [args.fvname]

    vars = []
    for infile in args.fvname:
        if '=' in infile:
            varname, filename = infile.split('=')
        else:
            filename = infile
            varname = filename.replace('.', '_').replace('/', '_')
        stream = open(filename, 'rb')
        fp = tempfile.TemporaryFile()
        if args.encrypt:
            pipe = Popen([join(dirname(realpath(__file__)), 'cmzp'), '-z'], stdin=PIPE, stdout=fp)
            sink = pipe.stdin
        else:
            sink =fp
        size = 0
        while True:
            buf = stream.read(1024)
            sink.write(buf)
            size += len(buf)
            if len(buf) < 1024:
                break
        if args.encrypt:
            sink.close()
        fp.seek(0)
        stream = fp

        vars.append(varname)

        fp = tempfile.TemporaryFile()
        fp.seek(0)

        write('const unsigned char %s[%u] = {\n' % (varname, size))
        while True:
            buf = stream.read(1024)
            write(', '.join([hex(b) for b in buf]))
            if len(buf) < 1024:
                write('\n};\n')
                break
            else:
                write(',')
        fp.close()

    if args.namespace:
        write('}\n')

    outfile = open(outpath + '.h', 'wb')
    macro_name = fname.replace('.', '_').upper() + '_H'
    write('#ifndef %s\n#define %s\n#ifdef __cplusplus\n' % (macro_name, macro_name))
    if args.namespace:
        write('namespace %s {\n' % (args.namespace))

    for var in vars:
        write('extern %s const unsigned char %s[%u];\n' % ('' if args.namespace else '"C"', var, size))

    if args.namespace:
        write('}\n')
    else:
        write('#else\n')
        for var in vars:
            write('extern const unsigned char %s[%u];\n' % (var, size))
    write('#endif\n')

    write('#endif //%s\n' % (macro_name))
