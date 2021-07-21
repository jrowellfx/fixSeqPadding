#!/usr/bin/env python3

# 3-Clause BSD License
# 
# Copyright (c) 2008-2021, James Philip Rowell,
# Alpha Eleven Incorporated
# www.alpha-eleven.com
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
# 
#  3. Neither the name of the copyright holder, "Alpha Eleven, Inc.",
#     nor the names of its contributors may be used to endorse or
#     promote products derived from this software without specific prior
#     written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# fixseqpadding - In the unusual case that the padding gets messed up
#         for an image-sequence, this utility will help you fix it.
#         The command-line util 'renumseq' requires that any sequence
#         be numbered with correct padding for it to work properly.
#
#         This only happened once in all the years I've beeng doing
#         CG post production. Inconsistent extra zeros (but not padded)
#         got tacked on to the begining of some sequences on a job that
#         I was working on (and needed to use renumseq on).
#
#         I took care of the bad padding on the spot with some adhoc
#         scripts, but was upset that my renumseq command wouldn't 
#         gracefully handle that situation.
#
#         I started adding the ability to fix bad padding to renumseq,
#         (Which led me to add the new error-listing capabilities of
#         'lsseq --showBadPadding') but renumseq started to get too
#         ugly with the added functionality and didn't fit the tool.
#         That led me to the conclusion to just write this util instead.
#                                                  James Rowell.

import re
import argparse
import os, sys
import textwrap
# import pathlib
import glob

import seqLister

VERSION = "1.0.0"

def warnSeqSyntax(silent, basename, seq) :
    if not silent :
        print(os.path.basename(sys.argv[0]),
            ": warning: invalid range [", seq, "] for seq ", basename,
            file=sys.stderr, sep='')

def main():

    fixNumList = []
    FIX_FULL_SEQ = True

    # Redefine the exception handling routine so that it does NOT
    # do a trace dump if the user types ^C while the program is running.
    #
    old_excepthook = sys.excepthook
    def new_hook(exceptionType, value, traceback):
        if exceptionType != KeyboardInterrupt and exceptionType != IOError:
            old_excepthook(exceptionType, value, traceback)
        else:
            pass
    sys.excepthook = new_hook

    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''
            Attempt to fix all the badly-padded frames in SEQ, otherwise try
            to fix only those listed with --fix. The pad size is determined
            by the padding of the smallest index specified in the SEQ argument
            or if --pad has been specified then force use of PAD digits.
            '''),
        usage="%(prog)s [OPTION]... [SEQ]...")

    p.add_argument("--version", action="version", version=VERSION)
    p.add_argument("--fix", action="store",
        dest="badFrameList", default=[], nargs='+', metavar="FRAME_SEQ_LIST",
        help="Fix bad-padding for frames listed in FRAME_SEQ_LIST. \
        Protip: Append '--' before the list of SEQs to delineate the end of the options if need be")
    #
    # Note: the following default for "pad" of "-1" means to leave
    # the padding on any given frame sequence unchanged.
    #
    p.add_argument("--pad", action="store", type=int,
        dest="pad", default=-1,
        metavar="PAD",
        help="force the padding of the fixed frame numbers to be PAD digits.")
    '''
    p.add_argument("--skip", action="store_false",
        dest="clobber", default=False,
        help="if fixing the padding of a frame in the SEQ would result in overwriting \
        an existing frame with a correctly padded name \
        then skip renaming the frame and print a warning. \
        The opposite of --force. [default]")
    p.add_argument("--force", action="store_true",
        dest="clobber",
        help="if fixing the padding of a frame in the SEQ would result in overwriting \
        an existing frame with a correctly padded name \
        then overwrite the frame. The opposite of --skip.")
    '''
    p.add_argument("--dryRun", action="store_true",
        dest="dryRun", default=False,
        help="Don't fix the padding for SEQ, just display how the \
        files would have been renamed. Forces --verbose" )
    p.add_argument("--silent", "--quiet", "-s", action="store_true",
        dest="silent", default=False,
        help="suppress warnings and errors")
    p.add_argument("--verbose", "-v", action="store_true",
        dest="verbose", default=False,
        help="list the mapping from old file-name to new file-name")
    p.add_argument("files", metavar="SEQ", nargs="*",
        help="image sequence in lsseq native format")

    args = p.parse_args()
    
    if args.files == [] :
        sys.exit(0)

    # Following list is ONLY zero-length if the option was NOT invoked,
    # because nargs='+' guarantees at LEAST one argument follows the option,
    # (otherwise argparser throws an error for the user and exits.)
    # 
    if len(args.badFrameList) > 0 :
        FIX_FULL_SEQ = False
        cruftList = []
        simpleBadPadList = []
        for a in args.badFrameList :
            simpleBadPadList.extend(a.replace(",", " ").split()) # Splits commas AND spaces.
        fixNumList = seqLister.expandSeq(simpleBadPadList, cruftList)
        if len(fixNumList) == 0 :
            if not args.silent :
                print(os.path.basename(sys.argv[0]),
                    ": error: invalid bad-padding list, use seqLister syntax",
                    file=sys.stderr, sep='')
            sys.exit(0)
        if len(cruftList) > 0 :
            if not args.silent :
                print(os.path.basename(sys.argv[0]),
                    ": error: invalid entries in the list of badly padded frames: ",
                    " ".join(cruftList),
                    file=sys.stderr, sep='')
            sys.exit(0)
        #
        # Over-ride all other options that could change the filenames.
        #
        fixNumList.sort() # To make for nicer verbose output later.

    if args.dryRun : # verbose to show how renumbering would occur.
        args.verbose = True

    # The following regular expression is created to match lsseq native sequence syntax
    # which means (number labels refer to parenthesis groupings **):
    #
    # 0 - one or more of anything,           followed by
    # 1 - a dot or underscore,               followed by
    #     an open square bracket,            followed by
    # 2 - a frame range,                     followed by
    #     a close square bracket then a dot, followed by
    # 3 - one or more letters, optionally one dot,
    #     then one or more letters, then one or more letters and numbers
    #     and the end of the line.
    #
    pattern = re.compile(r"(.+)([._])\[(-?[0-9]+-?-?[0-9]+)\]\.([a-zA-Z]+\.?[a-zA-Z]+[a-zA-Z0-9]*$)")

    for arg in args.files :
        abortSeq = False

        # Check if 'arg' is a sequence in valid lsseq native format
        #
        match = pattern.search(arg)
        if not match :
            if not args.silent :
                print(os.path.basename(sys.argv[0]), ": warning: ", arg,
                    " not a sequence or not in lsseq native format",
                    file=sys.stderr, sep='')
            continue

        v = match.groups()

        seq = [v[0], v[2], v[3]] # base filename, range, file-extension. (see above **)
        separator = v[1]

        # seq might be range with neg numbers. Assume N,M >= 0,
        # then there are only 5 seq cases that we need to be
        # concerned with: N, -N, N-M, -N-M, -N--M,
        # where -N or N is always less than or equal to -M or M.
        #
        negStart = 1.0
        negEnd = 1.0
        startStr = ""
        endStr = ""
        frRange = seq[1].split("-")

        if len(frRange) > 4 :
            warnSeqSyntax(args.silent, seq[0], seq[1])
            continue # Invalid syntax for range

        if len(frRange) == 1 : # Just N
            startStr = frRange[0]
            endStr = frRange[0]

        elif len(frRange) == 2 : # minus-N OR N-M
            if frRange[0] == '' : # Leading minus sign.
                negStart = -1.0
                negEnd = -1.0
                startStr = frRange[1]
                endStr = frRange[1]
            else :
                startStr = frRange[0]
                endStr = frRange[1]

        elif len(frRange) == 3 : # neg-N to M
            if frRange[0] != '' : # Not leading minus sign!
                warnSeqSyntax(args.silent, seq[0], seq[1])
                continue # Invalid syntax for range
            negStart = -1.0
            startStr = frRange[1]
            endStr = frRange[2]

        elif len(frRange) == 4 : # neg-N to neg-M
            if frRange[0] != '' or frRange[2] != '' : # Not leading minus signs!
                warnSeqSyntax(args.silent, seq[0], seq[1])
                continue # Invalid syntax for range
            negStart = -1.0
            negEnd = -1.0
            startStr = frRange[1]
            endStr = frRange[3]

        try :
            start = int(startStr)
        except ValueError : # Invalid syntax for range
            warnSeqSyntax(args.silent, seq[0], seq[1])
            continue

        try :
            end = int(endStr)
        except ValueError : # Invalid syntax for range
            warnSeqSyntax(args.silent, seq[0], seq[1])
            continue

        start *= negStart
        end *= negEnd

        if start > end :
            warnSeqSyntax(args.silent, seq[0], seq[1])
            continue

        startPad = len(startStr)
        if negStart < 0.0 :
            startPad += 1
        endPad = len(endStr)
        if negEnd < 0.0 :
            endPad += 1

        currentPad = 0
        if startPad < endPad :
            currentPad = startPad
        else :
            currentPad = endPad
        newPad = currentPad

        if args.pad >= 0 :
            newPad = args.pad

        correctFormatStr = "{0:0=-" + str(newPad) + "d}"

        if FIX_FULL_SEQ :
            fixNumList = list(range(int(start), int(end)+1))

        allSeqFiles = glob.glob(seq[0] + separator + "*[0-9]." + seq[2])
        origNames = []
        newNames = []
        for fnum in fixNumList :
            fnumMatchList = []
            for file in allSeqFiles :
                if re.search('.*' + separator + '-?0*' + str(fnum) + '\\.' + seq[2] + '$', file) :
                    fnumMatchList.append(file)

            # Zero len means no corresp file for fnum, so only do something if non-zero
            #
            if len(fnumMatchList) > 0 :

                correctName = seq[0] + separator + correctFormatStr.format(fnum) + '.' + seq[2]

                # Do nothing if the name is already correct, but print
                # WARNING if there's more than one file with that fnum.
                #
                if (correctName in fnumMatchList) : 
                    if len(fnumMatchList) > 1 and not args.silent :
                        sys.stdout.flush()
                        sys.stderr.flush()
                        print(os.path.basename(sys.argv[0]), ": warning: ", correctName,
                            " exists but there is a duplicate frame number ", fnum,
                            " with different padding",
                            file=sys.stderr, sep='')
                        sys.stderr.flush()
                else :
                    # Ambiguous - which file to repad?
                    #
                    if len(fnumMatchList) > 1 and not args.silent :
                        sys.stdout.flush()
                        sys.stderr.flush()
                        print(os.path.basename(sys.argv[0]), ": warning: ", correctName,
                            " corresponds to multiple files with bad-padding. Ambiguous rename. Skipping",
                            file=sys.stderr, sep='')
                        sys.stderr.flush()
                    else :
                        origNames.append(fnumMatchList[0])
                        newNames.append(correctName)

        i = 0
        numFiles = len(origNames)
        while i < numFiles :
            if args.verbose :
                print(origNames[i], " -> ", newNames[i], sep='')
            if not args.dryRun :
                os.rename(origNames[i], newNames[i])
            i += 1

if __name__ == '__main__':
    main()
