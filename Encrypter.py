#!/usr/bin/env python3

import base64
import binascii
import sys
import os
import PrintTools

class Ignition():
	def __init__(self,
				module,
				input,
				output,
				verbose,
				stdin,
				decrypt=False,
				overwrite=False):
		self.module = module
		self.decrypt = decrypt
		self.input = input
		self.output = output
		self.verbose = verbose
		self.stdin = stdin
		self.overwrite = overwrite
		self.vprint = PrintTools.PrintVerbose(verbose).vprint
		self.alwaysPrint = PrintTools.alwaysPrint

### This is our encryption processor
	def baseProcessor(self):
		if self.decrypt is False:
			message = 'encoder'
		else:
			message = 'decoder'

		if self.module == 'b64':
			if self.decrypt is False:
				self.encode = base64.b64encode
			else:
				self.encode = base64.b64decode

		elif self.module == 'b85':
			if self.decrypt is False:
				self.encode = base64.b85encode
			else:
				self.encode = base64.b85decode

		elif self.module == 'a85':
			if self.decrypt is False:
				self.encode = base64.a85encode
			else:
				self.encode = base64.a85decode
		self.vprint("reached the base64 processor\nutilizing {} Engine\n".format(self.module+'.'+message))

### Method for writing to stdout
	def write_stdout(self):
		try:
			if self.stdin == True:
				self.vprint('\nyour stdout is:')
				PrintTools.alwaysPrint(str(self.encode(self.input).decode()))
			else:
				self.vprint("writing file to stdout")
				with open(self.input, "rb") as file:
					output = file.read()
					self.vprint('your stdout is:')
					PrintTools.alwaysPrint(str(self.encode(output).decode()))
		except (binascii.Error, ValueError) as error:
			PrintTools.alwaysPrint("error: {}. did you mean to use the encrypt mode? are you using the proper encoder?".format(error))
			
###	Method for writing to file
	def write_file(self):
		try:		
			if self.stdin is True:
				with open(self.output, "wb") as outfile:
					outfile.write(self.encode(self.input))
			elif self.overwrite is True:
				print("we in overwrite mode")
				with open(self.input, "rb") as infile:
					file_bytes = infile.read()
					with open(self.input, "wb") as outfile:
						outfile.write(self.encode(file_bytes))
			else:
				with open(self.input, "rb") as infile, open(self.output, "wb") as outfile:
					outfile.write(self.encode(infile.read()))
		except (binascii.Error, ValueError) as error:
			PrintTools.alwaysPrint("error: {}. did you mean to use the encrypt mode? are you using the proper encoder?".format(error))
			os.remove(self.output) 
