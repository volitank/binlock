#!/usr/bin/env python3
import sys, os

# Disable
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Restore
def enablePrint():
    sys.stdout = sys.__stdout__

# Enable Verbot equals true
# vprint = PrintTools.PrintVerbose(True).vprint
# vprint('Verbosity is now enabled!')
def alwaysPrint(message):
    sys.__stdout__.write(message+'\n')

class PrintVerbose():
    def __init__(self, verbose):
        self.verbose = verbose

    def vprint(self, message):
        self.verbose
        if self.verbose is True:
            print(message)


