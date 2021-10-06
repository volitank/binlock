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

import logging
import hashlib
import argparse
from os import urandom
from getpass import getpass
from os.path import exists, basename
from sys import stdin, stdout, stderr, argv, exit
from bintools import encode, write_bytes, aes_decrypt, aes_encrypt, format_header, read_header, get_password

# Overwrite native error and help subclasses
class BinlockParser(argparse.ArgumentParser):
	def error(self, message):
		stderr.write('error: %s\n' % message)
		self.print_help()
		exit(1) 

def main():
	bin_name = basename(argv[0])
	formatter = lambda prog: argparse.HelpFormatter(prog,
													max_help_position=64)

	parent_parser = BinlockParser(	'parent',
									formatter_class=formatter,
									add_help=False)

	global_option = parent_parser.add_argument_group('global options')

	global_option.add_argument(	'-h', '--help', action='help', help='show this help message and exit')
	global_option.add_argument(	"-v", "--verbose",
								action="store_true",
								help='more verbose output')

	global_option.add_argument(	'-i', '--input',
								metavar='FILENAME',
								nargs='?',
								default=(None if stdin.isatty() else stdin.buffer),
								help=f'specify input file. If blank {bin_name} will attempt to use stdin. Takes priority over --stdin')

	global_option.add_argument(	'-o', '--output',
								metavar='FILENAME',
								nargs='?',
								default=stdout.buffer,
								const=True,
								help=f'specify an output file. If unused {bin_name} will generate a filename')

	global_option.add_argument(	'--debug',
								action="store_true",
								help='more output for debugging. --verbose is implied.')
	global_option.add_argument(	'--overwrite',
								action="store_true",
								help='this will overwrite the input file instead of creating a new file. cannot be used with standard input')

	global_option.add_argument(	'--version',
								action='version',
								version=f'{bin_name} v1.04')

	parser = BinlockParser(	formatter_class=formatter,
							parents=[parent_parser],
							add_help=False,
							usage=f'{bin_name} [--options] [-e b64, b85, a85] [-i input] [-o output]')

	encoder_option = parser.add_argument_group('encoder options')

	encoder_option.add_argument('-e', '--encoder',
								metavar='b64, b85, a85',
								choices=['b64', 'b85', 'a85'],
								nargs='?', default='b64',
								help='choose which encoder to use.')

	encoder_option.add_argument('--decode',
								action="store_true",
								help='switch to decoder. default is encoder')

	subparsers = parser.add_subparsers(	title='crypt',
										#description='This is the action for encryption and decryption',
										metavar=f'{bin_name} crypt --help',
										dest='crypt',
										help='print help for the encryption sub module'
										)

	parser_aes = subparsers.add_parser(	'crypt',
										formatter_class=formatter,
										usage=f'{bin_name} [crypt] [--options] [-i input] [-o output]',
										add_help=False,
										epilog=f'{bin_name} crypt currently only supports encryption with password.',
										parents=[parent_parser])

	crypt_option = parser_aes.add_argument_group('crypt options')

	crypt_option.add_argument(	'--decrypt',
								action='store_true', 
								help='switch to decryption. default is encryption')
	crypt_option.add_argument(	'--dump-header',
								action='store_true',
								help='prints header information and exits')

	argument = parser.parse_args()
	encoder = argument.encoder
	decrypt = argument.decode
	source = argument.input
	output = argument.output
	verbose = argument.verbose
	debug = argument.debug
	overwrite = argument.overwrite
	crypt = argument.crypt
	if crypt:
		decrypt = argument.decrypt
		dump = argument.dump_header

	if debug:
		logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG, datefmt='[%Y-%m-%d %H:%M:%S]')
	elif verbose:
		logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO, datefmt='[%Y-%m-%d %H:%M:%S]')
	else:
		logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='[%Y-%m-%d %H:%M:%S]')

	eprint = logging.error
	vprint = logging.info
	dprint = logging.debug

	# Check if we're tyring to use overwrite with source. 
	if overwrite and source == stdin.buffer:
		eprint("--overwrite cannot be used with standard input")
		parser.parse_args(['--help'])
		exit(1)

	# Make sure there is source. If not error and print --help.
	if source is None:
		eprint("no input detected")
		parser.parse_args(['--help'])
		exit(1)
	else:
		if source != stdin.buffer:
			if not exists(source):
				eprint("file: {} does not exist!".format(source))
				exit(1)

	# If verbose or debug is enabled we should print to console.
	dprint('arguments:')
	for arg in vars(argument):
		dprint('[{} = {}]'.format(arg, str(getattr(argument, arg))))

	# If output isn't specified we need to make an output file.
	if overwrite is True:
		output = source
	else:
		if output is True:
			if crypt:
				file_extension = 'aes'
			else:
				file_extension = encoder
			if decrypt:
				file_extension = 'plain'
			vprint("no output detected. creating file name")
			if source == stdin.buffer:
				output = ('stdin'+'.'+file_extension)
			else:
				output = (source+'.'+file_extension)

	if crypt is None:
		write_bytes(encode(source, encoder, decrypt), output)
	if dump:
		header = read_header(source, True)
		if source == stdin.buffer:
			source = 'stdin'
		print("binlock header information:\n")
		print(f"[file = {source}]")
		for name, value in header.items():
			print(f"[{name} = {value}]")
		exit(0)
	else:
		if decrypt:
			salt, hash, aad, iv, tag = read_header(source)
			password = getpass().encode()
			if hash == hashlib.new('sha512', salt+password).digest():
				print('password verified')
				key = hashlib.pbkdf2_hmac('sha512', password, salt, 10000, 32)
				del password
			else:
				print('incorrect password')
				exit(1)
			plain_text = aes_decrypt(source, key, iv, aad, tag)
			write_bytes(plain_text, output)
		else:
			# Generate salt and iv
			salt = urandom(32)
			iv = urandom(16)
			aad = urandom(16)
			password = get_password()
			hash = hashlib.new('sha512', salt+password).digest()
			key = hashlib.pbkdf2_hmac('sha512', password, salt, 10000, 32)
			# We want to remove password from memory as soon as we're done with it.
			del password

			#header = format_header(hash, salt, iv)
			crypt_data, tag = aes_encrypt(source, key, iv, aad)
			header = format_header(hash, salt, iv, aad, tag)
			append_head = header+crypt_data
			write_bytes(append_head, output)

if __name__ == "__main__":
	main()
