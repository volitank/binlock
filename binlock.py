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
import argparse
from os.path import exists
from encoder import encode, write_bytes
from sys import stdin, stdout, stderr, exit

# Overwrite native error and help subclasses
class BinlockParser(argparse.ArgumentParser):
	def error(self, message):
		stderr.write('error: %s\n' % message)
		self.print_help()
		exit(1) 

def main():
	formatter = lambda prog: argparse.HelpFormatter(prog,
													max_help_position=64)
	parser = BinlockParser(	formatter_class=formatter,
							usage='%(prog)s [--options] [-e b64, b85, a85] [-i input] [-o output]')
	parser.add_argument("-v", "--verbose",
						action="store_true",
						help='more verbose output')

	parser.add_argument('-e', '--encoder',
						metavar='b64, b85, a85',
						choices=['b64', 'b85', 'a85'],
						nargs='?', default='b64',
						help='choose which encoder to use.')

	parser.add_argument('-i', '--input',
						metavar='FILENAME',
						nargs='?',
						default=(None if stdin.isatty() else stdin.buffer),
						help='specify input file. If blank %(prog)s will attempt to use stdin. Takes priority over --stdin')

	parser.add_argument('-o', '--output',
						metavar='FILENAME',
						nargs='?',
						default=stdout.buffer,
						const=True,
						help='specify an output file. If unused %(prog)s will generate a filename')

	parser.add_argument('--decode',
						action="store_true",
						help='switch to decoder. default is encoder',)

	parser.add_argument('--overwrite',
						action="store_true",
						help='this will overwrite the input file instead of creating a new file. cannot be used with standard input')

	parser.add_argument("--debug",
						action="store_true",
						help='more output for debugging. --verbose is implied and will print even in --stdout mode',)

	parser.add_argument('--version',
						action='version',
						version='%(prog)s v1.03')

	argument = parser.parse_args()
	encoder = argument.encoder
	decrypt = argument.decode
	source = argument.input
	output = argument.output
	verbose = argument.verbose
	debug = argument.debug
	overwrite = argument.overwrite

	if debug:
		logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG, datefmt='[%Y-%m-%d %H:%M:%S]')
		print('debug')
	elif verbose:
		logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO, datefmt='[%Y-%m-%d %H:%M:%S]')
		print('verbose')
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
		output = True
	if output is True:
		vprint("no output detected. creating file name")
		if source == stdin.buffer:
			if decrypt is True:
				output =('stdin'+'.plain')
			else:
				output = ('stdin'+'.'+encoder)
		else:
			if decrypt is True:
				output = (source+'.plain')
			else:
				output = (source+'.'+encoder)
			if overwrite is True:
				output = source

	#test = encode(source, encoder, decrypt)

	write_bytes(encode(source, encoder, decrypt), output)
if __name__ == "__main__":
	main()