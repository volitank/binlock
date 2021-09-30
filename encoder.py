#!/usr/bin/env python3

# This file is part of binlock.

# binlock is a simple encoder program for base64, base85 and ascii85.
# Copyright (C) 2021 Volitank

# binlock is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# binlock is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with binlock.  If not, see <https://www.gnu.org/licenses/>.

import logging
from binascii import Error
from os.path import exists
from sys import stdin, stdout, exit
from base64 import b64encode, b64decode, b85encode, b85decode, a85encode, a85decode

eprint = logging.error
vprint = logging.info
dprint = logging.debug

def encode(source, module: str = 'b64', decode: bool = False):
	"""Function for encoding and decoding source. Returns bytes

	Arguments:
		source: The source whether '/path/to/filename', sys.stdin, or even a simple string
		module: The module to encode with [b64, b85, a85]
		decode: Set to True to switch to decoding
	Usage::

		encode('/path/to/filename.txt', decode=True)
		"This will encode your file to base64"
	"""
	# Encoder defaults to base64
	if module == 'b64':
		if decode:
			encode = b64decode
		else:
			encode = b64encode
	# Base85 Initialization
	elif module == 'b85':
		if decode:
			encode = b85decode
		else:
			encode = b85encode
	# Base85 Initialization
	elif module == 'a85':
		if decode:
			encode = a85decode
		else:
			encode = a85encode
	else:
		eprint(f"module {module} isn't valid")
	vprint(f"utilizing {module} encoder")

	# This is where we start the actual encoding / decoding
	try:
		# Handle if source is stdin.
		if source == stdin.buffer:
			# Read stdin buffer and store it
			input_bytes = source.read()
			# Encode stdin buffer
			encode_out = encode(input_bytes)
			dprint("--stdin bytes is {}".format(input_bytes)) 
		# This will handle a normal string passed as source
		if type(source) is str:
			if not exists(source):
				vprint("file: {} does not exist! Formatting as string".format(source))
				# convert the string to bytes and then encode it.
				encode_out = encode(source.encode('utf 8'))
			else:
				with open(source, "rb") as infile:
					vprint("reading file: '{}'".format(infile.name))
					# Encode the input file
					encode_out = encode(infile.read())
		# This handles a bytes type source.
		if type(source) is bytes:
				vprint("Bytes detected. Encoding.")
				encode_out = encode(source)
	except (Error, ValueError) as error:
		eprint(str(error))
		eprint("did you mean to use the encrypt mode? are you using the proper encoder?")
		exit(1)
	except PermissionError as error:
		error = str(error).replace('[Errno 13]', '').lstrip(' ')
		eprint(error)
		exit(1)
	return encode_out

###	Method for writing to file
def write_bytes(source: bytes, output=stdout.buffer):
	"""Function for writing bytes to output.

	Arguments:
		source: should be bytes
		output: can be a file or default stdout.buffer
	Usage::

		bytes = encode('filename.txt')
		write_bytes(bytes, 'writefile.b64')
	"""
	try:		
		if output == stdout.buffer:
			# Write to stdout
			stdout.buffer.write(source)
			exit(0)
		# We open the output file			
		with open(output, "wb") as outfile:
			vprint("writing to {}".format(output))
			# Write encoded input to file
			outfile.write(source)
			exit(0)
	except (Error, ValueError) as error:
		eprint(str(error))
		eprint("did you mean to use the encrypt mode? are you using the proper encoder?")
		exit(1)
	except PermissionError as error:
		error = str(error).replace('[Errno 13]', '').lstrip(' ')
		eprint(error)
		exit(1)