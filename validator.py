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
#PATHS_GISMU_DIRS = ['experimental_gismu']

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

def experimentalFromFilename(gismuFile):
    import re
    return re.search('experimental_gismu', gismuFile) is not None

GISMU = {}

def load_gismu_file(gismuFile):
    f = open(gismuFile, 'r')
    gStr = gismuFromFilename(gismuFile)
    t = f.read()
    gObj = gismu.yaml2Gismu(gStr, t)
    if experimentalFromFilename(gismuFile):
        gObj.setExperimental(True)
    GISMU[gObj.get()] = gObj

def getGismuDirs():
    import os
    root = os.path.dirname(os.path.realpath(__file__))
    return [os.path.join(root, d) for d in PATHS_GISMU_DIRS]

class CollectionVisitor:
    def __init__(self):
        pass

    def visitGismu(self, word, data):
        pass

    def visitCollection(self):
        for k,v in GISMU.items():
            self.visitGismu(k,v)

    def print(self):
        pass

    def getResult(self):
        return True

class LevenshteinPairMetric:
    # Implementation from https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
    def levenshtein(seq1, seq2):
        oneago = None
        thisrow = range(1, len(seq2) + 1) + [0]
        for x in xrange(len(seq1)):
            twoago, oneago, thisrow = oneago, thisrow, [0] * len(seq2) + [x + 1]
            for y in xrange(len(seq2)):
                delcost = oneago[y] + 1
                addcost = thisrow[y - 1] + 1
                subcost = oneago[y - 1] + (seq1[x] != seq2[y])
                thisrow[y] = min(delcost, addcost, subcost)
        return thisrow[len(seq2) - 1]

class CollectionMetrics(CollectionVisitor):
    def __init__(self):
        self.gismuCount = 0
        self.definitionLang = {}

    def visitGismu(self, word, gismu):
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

class GismuInfo:
    def __init__(self, word, gismuObj):
        pass

class PairVisitor:
    def __init__(self):
        pass

    def visitPair(self, a, b):
        pass

class ConflictingPairValidator(PairVisitor):
    def __init__(self, validator):
        self.validator = validator

    def visitPair(self, a, b):
        # CLL 4.14 - conflicting gismu: too similar
        for aSimilar, aIdx, aLetter, rLetter in a.getSimilarForms():
            if b.get() == aSimilar:
                self.validator.addValidationError("gismu too similar: %s %s  (differs by %s to %s)" % (str(b), str(a), aLetter, rLetter))
                return
        for bSimilar, bIdx, bLetter, rLetter in b.getSimilarForms():
            if a.get() == bSimilar:
                self.validator.addValidationError("gismu too similar: %s %s  (differs by %s to %s)" % (str(a), str(b), bLetter, rLetter))
                return

class ConflictingRafsiValidator(PairVisitor):
    def __init__(self, validator):
        self.validator = validator

    def visitPair(self, a, b):
        # check for gismu that have the same rafsi
        intersect = set(a.getRafsi()).intersection(b.getRafsi())
        if intersect:
            self.validator.addValidationError("gismu have same rafsi: %s %s  (common rafsi: %s)" % (str(b), str(a), str(intersect)))


class FinalVowelValidator(PairVisitor):
    def __init__(self, validator):
        self.validator = validator

    def visitPair(self, a, b):
        # CLL 4.4 - no two gismu differ only in the final vowel (exception: broda, brode, brodi, brodo, and brodu)
        if a.get()[0:4] == b.get()[0:4]:
            if (a.get()[0:4] == "brod") and (b.get()[0:4] == "brod"):
                return
            self.validator.addValidationError("no two gismu can differ only in the final vowel: %s %s" % (str(a), str(b)))

# Validating all gismu as a whole collection
class CollectionValidator(CollectionVisitor):
    def __init__(self):
        self.data = set()
        self.dataDuplicates = {}
        self.setDirty()

    def setDirty(self):
        self.failed = None   # None => dirty, need to validate()
        self.validationErrors = []

    def visitGismu(self, gismu, g):
        self.failed = None

        # Cache to find duplicates
        if g not in self.data:
            self.data.add(g)
        else:
            if gismu not in self.dataDuplicates.keys():
                self.dataDuplicates[gismu] = []
            self.dataDuplicates[gismu].append(self.data.remove(gismu))
            self.dataDuplicates[gismu].append(g)

    def addValidationError(self, ve):
        self.failed = True
        self.validationErrors.append(ve)

    def validate(self):
        if self.failed is not None:
            # hasn't changed since the last time we calculated it
            return
        self.failed = False
        self.validationErrors = []

        # CLL 4.14 - conflicting gismu: identical
        if len(self.dataDuplicates.keys()) > 0:
            for k in self.dataDuplicates.keys():
                self.addValidationError("duplicate gismu: %s" % (k))

        # Get sorted list of gismu
        glist = []
        glist.extend(self.data)
        for k,v in self.dataDuplicates.items():
            glist.extend(v)
        glist = sorted(glist)

        # Adjacent pairwise checks
        adjacentPairwiseChecks = [FinalVowelValidator(self)]
        for i in range(1, len(glist)):
            a = glist[i-1]
            b = glist[i]
            for check in adjacentPairwiseChecks:
                check.visitPair(a, b)

        # Pairwise checks
        pairwiseChecks = [ConflictingPairValidator(self), ConflictingRafsiValidator(self)]
        for i in range(0, len(glist)):
            for j in range(i+1, len(glist)):
                a = glist[i]
                b = glist[j]

                for check in pairwiseChecks:
                    check.visitPair(a,b)


    def print(self):
        self.validate()
        for ve in self.validationErrors:
            print(ve)

    # True = validate ok
    def getResult(self):
        self.validate()
        return not self.failed


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

    print("...loaded %d (%d failed to load)" % (countProcessed, countFail))

    cmet = CollectionMetrics()
    cmet.visitCollection()

    cval = CollectionValidator()
    cval.visitCollection()

    print("Summary:")
    cmet.print()
    cval.print()

    exitcode = 0
    if countFail:
        exitcode=1
    import sys
    sys.exit(exitcode)

if __name__ == "__main__":
    main()

