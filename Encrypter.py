#!/usr/bin/env python3

import base64
import binascii
import sys
import PrintTools

class Ignition():
	def __init__(self, module, encrypt, input, output, verbose, stdin):
		self.module = module
		self.encrypt = encrypt
		self.input = input
		self.output = output
		self.verbose = verbose
		self.stdin = stdin
		self.vprint = PrintTools.PrintVerbose(verbose).vprint

### This is our encryption processor
	def processor64(self):
		if self.encrypt == 'encrypt':
			self.encode = base64.b64encode
		elif self.encrypt == 'decrypt':
			self.encode = base64.b64decode
		self.vprint("reached the base64 processor\nutilizing {} Engine\n".format(self.module+'.'+self.encrypt))

### Method for writing to stdout
	def write_stdout(self):
		if self.stdin == True:
			self.vprint('\nyour stdout is:')
			sys.__stdout__.write(str(self.encode(self.input).decode()))
		else:
			self.vprint("writing file to stdout")
			with open(self.input, "rb") as file:
				output = file.read()
				self.vprint('your stdout is:')
				self.output.write(str(self.encode(output).decode()))

###	Method for writing to file
	def write_file(self):
		try:		
			if self.stdin == True:
				with open(self.output, "wb") as outfile:
					outfile.write(self.encode(self.input))
			else:
				with open(self.input, "rb") as infile, open(self.output, "wb") as outfile:
					outfile.write(self.encode(infile.read()))
		except binascii.Error as error:
			print("error: invalid base64-encoded string. did you mean to use the encrypt mode?")
			self.vprint('error: {}'.format(error))
