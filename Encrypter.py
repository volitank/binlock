#!/usr/bin/env python3

import base64
import binascii
import io
import sys
import PrintTools

class Ignition():
    def __init__(self, module, encrypt, input, output, verbose):
        self.module = module
        self.encrypt = encrypt
        self.input = input
        self.output = output
        self.verbose = verbose
        self.vprint = PrintTools.PrintVerbose(verbose).vprint

### This is our encryption processor
    def processor64(self):
        if self.encrypt == 'encrypt':
            self.encode = base64.b64encode
        elif self.encrypt == 'decrypt':
            self.encode = base64.b64decode
        self.vprint("reached the base64 processor\nutilizing {} Engine\n".format(self.module+'.'+self.encrypt))
        self.stdin_check()

####### If there is --stdin we need to handle that
    def stdin_check(self):
        if self.input == sys.stdin:
            self.input_string = self.input.read()
            self.input_bytes = (str(self.input_string)).encode('utf 8')
            #self.input = (str(self.input_string).rstrip()).encode('utf 8')
            self.vprint("The --stdin string is {}".format(self.input_string))
            self.vprint("The --stdin bytes is {}".format(self.input_bytes))
            if hasattr(self.output, 'name') and self.output.name == '<stdout>':
                self.vprint('\nyour stdout is:')
                sys.__stdout__.write(str(self.encode(self.input_bytes).decode()))
            else:
                self.vprint("Not using --stdout. moving to file handler.")
                self.stdin_file()
        else:
            #sys.__stdout__.write(self.input)
            if hasattr(self.output, 'name') and self.output.name == '<stdout>':
                with open(self.input, "rb") as file:
                    output = file.read()
                    self.vprint('your stdout is:')
                    self.output.write(str(self.encode(output).decode()))
            else: 
                self.two_file()

########### This section is for --stdin and outfile
    def stdin_file(self):
        with open(self.output, "wb") as outfile:
            try:
                outfile.write(self.encode(self.input_bytes))
            except binascii.Error as error:
                print("error: invalid base64-encoded string. did you mean to use the encrypt mode?")
                self.vprint('error: {}'.format(error))
        
####### This section is for infile and outfile.
    def two_file(self):
        with open(self.input, "rb") as infile, open(self.output, "wb") as outfile:
            try:
                outfile.write(self.encode(infile.read()))
            except binascii.Error as error:
                print("error: invalid base64-encoded string. did you mean to use the encrypt mode?")
                self.vprint('error: {}'.format(error))