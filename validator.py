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

PATHS_GISMU_DIRS = ['gismu', 'experimental_gismu']

class RESULT(object):
    def max(a, b):
        if a.getValue() < b.getValue():
            return b
        else:
            return a

class PASS(RESULT):
    def getName():
        return 'PASS'
    def getValue():
        return 0
class WARNING(RESULT):
    def getName():
        return 'WARNING'
    def getValue():
        return 1
class FAIL(RESULT):
    def getName():
        return 'FAIL'
    def getValue():
        return 2

CONSONANTS = ['b', 'c', 'd', 'f', 'g', 'j', 'k', 'l', 'm', 'n', 'p', 'r', 's', 't', 'v', 'x', 'z']
VOWELS = ['a', 'e', 'i', 'o', 'u']

def isCorV(ch):
    if ch.lower() in CONSONANTS:
        return 'c'
    if ch.lower() in VOWELS:
        return 'v'
    if ch.lower() is 'y':
        # sort of a consonant
        return 'y'
    return '#'

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

class YAMLValidator:
    def __init__(self):
        pass

class Metrics:
    def __init__(self):
        self.gismuCount = 0
        self.definitionLang = {}

    def add(self, other):
        self.gismuCount += other.gismuCount
        for k,v in other.definitionLang.items():
            if k in self.definitionLang.keys():
                self.definitionLang[k] += v
            else:
                self.definitionLang[k] = v

    def addGismu(self, gismu):
        self.gismuCount += 1

    def addDefLang(self, lang):
        if lang in self.definitionLang.keys():
            self.definitionLang[lang] += 1
        else:
            self.definitionLang[lang] = 1

    def print(self):
        print("%d gismu" % (self.gismuCount))
        for k,v in self.definitionLang.items():
            print("%d defs in language %s" % (v, k))

class GismuValidator(YAMLValidator):
    def __init__(self, gismu):
        self.gismu = gismu
        self.metrics = Metrics()

    def checkGismu(self, ast):
        sections = {'word': GismuValidator.checkGismuWord,
                'rafsi': GismuValidator.checkGismuRafsi,
                'examples': GismuValidator.checkGismuExamples,
                'definitions': GismuValidator.checkGismuDefinitions }
        result = PASS
        for k,v in ast.items():
            sub = sections.get(k)
            if sub is not None:
                subResult = sub(self, v)
                result = RESULT.max(result, subResult)
            else:
                print("unrecognised section: %s" % (k))
        return result
    def checkGismuWord(self, ast):
        self.metrics.addGismu(self.gismu)

        # Must match filename
        if ast != self.gismu:
            "gismu does not match file name"
            return FAIL

        # CLL 4.4 - always have five letters
        if len(self.gismu) != 5:
            "gismu must always have five letters"
            return FAIL

        # CLL 4.4 - start with a consonant and end with a single vowel
        # CLL 4.4 - always contain exactly one consonant pair
        cvString = ''
        for l in self.gismu:
            cvString += isCorV(l)
        if cvString not in ['ccvcv', 'cvccv']:
            "gismu form is invalid"
            return FAIL

        # TODO: check for conflicting gismu (see CLL 4.14.4)
        return PASS

    def checkGismuRafsi(self, ast):
        # TODO: check rasfi are well formed
        return PASS

    def checkGismuExamples(self, ast):
        # TODO: check examples are well formed
        return PASS

    def checkGismuDefinitions(self, ast):
        for k,v in ast.items():
            self.metrics.addDefLang(k)
        # TODO: check definitions are well formed
        return PASS

def gismuFromFilename(gismuFile):
    import os
    import re
    gfile = os.path.basename(gismuFile)
    g = re.match('(.....)\.yaml', gfile)
    if g:
        return g.group(1)
    return None

def validate_gismu(gismuFile):
    f = open(gismuFile, 'r')
    t = f.read()
    import yaml
    y = None
    try:
        y = yaml.load(t)
    except yaml.YAMLError as exc:
        print(exc)
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            print("Error position: (%s:%s)" % (mark.line+1, mark.column+1))
    if y is None:
        return FAIL

    g = gismuFromFilename(gismuFile)
    gv = GismuValidator(g)
    result = gv.checkGismu(y)
    return (result, gv.metrics)

def getGismuDirs():
    import os
    root = os.path.dirname(os.path.realpath(__file__))
    return [os.path.join(root, d) for d in PATHS_GISMU_DIRS]

def main():
    gismu_dirs = getGismuDirs()
    count = {PASS: 0, WARNING: 0, FAIL: 0}
    total = Metrics()
    for x in getFileList(gismu_dirs, skipRegex='.*\.md$'):
        (result, metrics) = validate_gismu(x)
        print("%s: %s" % (x, result.getName()))
        count[result] = count[result] + 1
        total.add(metrics)

    print("Summary:")
    for r,c in count.items():
        print("%s %d" % (r.getName(), c))
    total.print()

    exitcode = 0
    if count[FAIL]:
        exitcode=1
    import sys
    sys.exit(exitcode)

if __name__ == "__main__":
    main()

