#!/usr/bin/env python3

# 2-clause BSD license
"""
Copyright (c) 2014, Andrew Browne <dersaidin@dersaidin.net>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of the FreeBSD Project.
"""

#PATHS_GISMU_DIRS = ['gismu', 'experimental_gismu']
PATHS_GISMU_DIRS = ['experimental_gismu']

from pygimste import gismu

def getFileList(args, realpath=True, skipRegex=None):
    import os
    initial = []
    if args:
        # Start from the arguments
        for a in args:
            initial.append(a)
    else:
        # If no arguments are given, start from the current working directory
        initial.append(os.getcwd())

    # Build up the list of files under the initial paths
    result = []
    for init in initial:
        if os.path.isdir(init):
            # Recurse into directories
            for root, dirs, files in os.walk(init):
                for f in files:
                    path = os.path.join(root,f)
                    result.append(path)
        else:
            result.append(init)

    # Realpath results
    if realpath:
        result = [os.path.realpath(x) for x in result]

    if skipRegex:
        import re
        skipRE = re.compile(skipRegex)
        result = [x for x in result if not skipRE.match(x) ]

    return sorted(result)


def gismuFromFilename(gismuFile):
    import os
    import re
    gfile = os.path.basename(gismuFile)
    g = re.match('(.....)\.yaml', gfile)
    if g:
        return g.group(1)
    return None

GISMU = {}

def load_gismu_file(gismuFile):
    f = open(gismuFile, 'r')
    gStr = gismuFromFilename(gismuFile)
    t = f.read()
    gObj = gismu.yaml2Gismu(gStr, t)
    GISMU[gObj.get()] = gObj

def getGismuDirs():
    import os
    root = os.path.dirname(os.path.realpath(__file__))
    return [os.path.join(root, d) for d in PATHS_GISMU_DIRS]

class Metrics:
    def __init__(self):
        self.gismuCount = 0
        self.definitionLang = {}

    def addGismu(self, gismu):
        self.gismuCount += 1
        for lang, defs in gismu.getDefinitions().items():
            for d in defs:
                assert(lang == d.getLang())
                self.addDefLang(d.getLang())

    def addDefLang(self, lang):
        if lang in self.definitionLang.keys():
            self.definitionLang[lang] += 1
        else:
            self.definitionLang[lang] = 1

    def print(self):
        print("%d gismu" % (self.gismuCount))
        for k,v in self.definitionLang.items():
            print("%d defs in language %s" % (v, k))

# Validating all gismu as a whole collection
class CollectiveValidator:
    def __init__(self):
        self.data = {}
        self.dataDuplicates = {}

    def addGismu(self, gismu):
        g = GismuInfo(gismu, rasfi)
        if gismu not in self.data.keys():
            self.data[gismu] = g
        else:
            if gismu not in self.dataDuplicates.keys():
                self.dataDuplicates[gismu] = []
            self.dataDuplicates[gismu].append(self.data.pop(gismu))
            self.dataDuplicates[gismu].append(g)

def main():
    gismu_dirs = getGismuDirs()
    countFail = 0
    countProcessed = 0
    for x in getFileList(gismu_dirs, skipRegex='.*\.md$'):
        countProcessed += 1
        try:
            load_gismu_file(x)
        except gismu.YamlParseException as exc:
            countFail += 1
            print(exc)
        except gismu.GismuValidationException as exc:
            countFail += 1
            print(exc)
        except Exception as exc:
            # Unknowon/unexpected
            raise exc
        if countProcessed % 100 == 0:
            print("...loaded %d" % (countProcessed))

    print("...loaded %d" % (countProcessed))

    total = Metrics()
    for k,v in GISMU.items():
        total.addGismu(v)

    print("Summary:")
    print("%d failed to load" % (countFail))
    total.print()

    exitcode = 0
    if countFail:
        exitcode=1
    import sys
    sys.exit(exitcode)

if __name__ == "__main__":
    main()

