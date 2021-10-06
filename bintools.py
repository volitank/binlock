#!/usr/bin/env python3

# This file is part of binlock.

# binlock is a simple encoding and encryption program.
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

import json
import logging
from typing import Union
from os.path import exists
from binascii import Error
from getpass import getpass
from sys import stdin, stdout, exit
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from base64 import b64encode, b64decode, b85encode, b85decode, a85encode, a85decode

eprint = logging.error
vprint = logging.info
dprint = logging.debug

# Encoding and Decoding function
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

# AES Encyption function
def aes_encrypt(source, key, iv, aad):
	"""Encrypts source with key, iv and aad.

	Arguments:
		source: Should be bytes.
		key: Only 128, 192, and 256 bit keys (16, 32, 64 bytes).
		iv: Initialization_Vector(IV); must be between 8 and 128 bytes (64 and 1024 bits).
		aad: Authenticate Additional Data; use the same type and size key you used for IV. 

	Returns encrypted data and the ecnryptor tag(needed to decrypt)
	
	XTS either 256 or 512 = tweak(IV) must be 128-bits (16 bytes)

	you can use the same input for key, iv and aad but it's not reccomended.
	"""
	cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
	encryptor = cipher.encryptor()
	encryptor.authenticate_additional_data(aad)
	if source == stdin.buffer:
		data = encryptor.update(stdin.buffer.read()) + encryptor.finalize()
	else:
		with open(source, 'rb') as file:
			data = encryptor.update(file.read()) + encryptor.finalize()
	return data, encryptor.tag

# AED Decryption function.
def aes_decrypt(source, key, iv, aad, tag):
	"""Decrypts source with key, iv and aad.

	Arguments:
		source: Should be bytes.
		key: Only 128, 192, and 256 bit keys (16, 32, 64 bytes).
		iv: Initialization_Vector(IV); must be between 8 and 128 bytes (64 and 1024 bits).
		aad: Authenticate Additional Data; use the same type and size key you used for IV.
		tag: This was returned from the encryption process
	
	Realistically this information will be pulled from the binlock header.

	Functionality for plain crypto without headers will be implemented eventually.
	"""
	# Tag must be at least 16 bytes
	from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
	cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag))
	decryptor = cipher.decryptor()
	decryptor.authenticate_additional_data(aad)
	if source == stdin.buffer:
		data = decryptor.update(stdin.buffer.read()) + decryptor.finalize()
	else:
		with open(source, 'rb') as file:
			file.seek(512)
			data = decryptor.update(file.read()) + decryptor.finalize()
	return data

# Askes user for a password
def get_password():
	"Asks user for password, confirms it and returns it in bytes"
	while True:
		password = getpass("password:").encode()
		confirmpass = getpass("confirm password:").encode()
		if password == confirmpass:
			vprint("passwords match")
			return password
		del password
		eprint("passwords don't match! try again.")

### Creates our header
def format_header(hash, salt, iv, aad, tag) -> bytes:
	"""Formats and pads the binlock header

	Returns a bytes object that you will append to data.
	"""
	header = {}
	header.update({'format':'binlock'})
	header.update({'hash':hash.hex()})
	header.update({'salt':salt.hex()})
	header.update({'iv':iv.hex()})
	header.update({'aad':aad.hex()})
	header.update({'tag':tag.hex()})
	jheader = json.dumps(header).encode()
	binlock = (b'\x00' * 4)+b'#binlock'+(b'\x00' * 4)
	header_size = len(binlock+jheader)
	if header_size != 512:
		pad = 512 - header_size
		header = binlock+jheader+(b'\x00' * pad)
		return header

### Reads the header of our file
def read_header(source, raw: bool = False) -> Union[dict,tuple]:
	"""returns salt, hash, add, iv and tag

	raw: If True it will return the full header

	If the source header can't be read it errors
	"""
	try:
		if source == stdin.buffer:
			header = stdin.buffer.read(512).decode().replace('\x00', '')
		else:
			with open(source, 'rb') as file:
				header = file.read(512).decode().replace('\x00', '')
		if '#binlock' not in header:
			raise ValueError
		header = json.loads(header.removeprefix('#binlock'))
		if raw:
			return header
		else:
			salt = bytes.fromhex(header.get('salt'))
			hash = bytes.fromhex(header.get('hash'))
			aad = bytes.fromhex(header.get('aad'))
			iv = bytes.fromhex(header.get('iv'))
			tag = bytes.fromhex(header.get('tag'))
			return salt, hash, aad, iv, tag
	except ValueError as e:
		if source == stdin.buffer:
			source = 'stdin'
		eprint(f"'{source}' is not a valid binlock file")
		exit(1)

###	Function for writing to file
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

