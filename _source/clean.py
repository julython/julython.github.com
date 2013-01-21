#!/usr/bin/env python
"""
Clean only auto generated files.
"""
import os
import shutil

IGNORE = ['README.md', 'CNAME', 'talks']

def clean(pwd, test=False):
    for name in os.listdir(pwd):
        if name in IGNORE or name[0] in ['.', '_']:
            continue
        if test:
            print name
        else:
            print "removing %s" % name
            f = os.path.join(pwd, name)
            if os.path.isdir(f):
                shutil.rmtree(os.path.join(pwd, name))
            else:
                os.remove(f)

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser(__doc__)
    parser.add_option('-t', '--test', action="store_true", dest='test', 
        default=False, help="run the test suite")
    
    options, args = parser.parse_args()
    
    # else we should have been passed a filename
    if len(args) < 1:
        parser.error("Please enter a file to parse")
    
    clean(args[0], test=options.test)
