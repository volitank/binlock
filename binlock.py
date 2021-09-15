#!/usr/bin/env python3

import argparse
import sys
import os
import PrintTools
import Encrypter

# Define our custom help message
prog = os.path.basename(sys.argv[0])
help_message = "\
usage: {0} [--options] [b64,b85,a85] [input_file] [-o output_file]\n\n\
positional arguments:\n\
  [b64, b85, a85]       choose which encoder to use.\n\
  input_file            specify input file. If blank {0} will attempt to use stdin.\n\n\
optional arguments:\n\
  -h, --help            show this help message and exit\n\
  -s, --stdout          supress all messages except for the encrypted/decrypted output. overrides output-file\n\
  -o, --output-file     specify an output file. if ommited {0} will generate a filename.\n\
  -v, --verbose         more verbose output\n\
  --decode              switch to decoder. default is encoder\n\
  --overwrite           this will overwrite the input file instead of creating a new file\n\
  --debug               more output for debugging. --verbose is implied and will print even in --stdout mode\n\
  --version             show program\'s version number and exit".format(prog)

# Overwrite native error and help subclasses
class BinlockParser(argparse.ArgumentParser):
	def error(self, message):
		sys.stderr.write('error: %s\n' % message)
		self.print_help()
		sys.exit(2)

	def print_help(self, file=None):
		if file is None:
			file = sys.stdout
		self._print_message(help_message+'\n', file)

def main():
	parser = BinlockParser(add_help=False)
	# If I decide to keep custom help I'll edit this section
	parser.add_argument(dest='module', metavar='[b64, b85, a85]', help='choose which encoder to use.', choices=['b64', 'b85', 'a85'])
	parser.add_argument('-h', '--help', action="store_true")
	parser.add_argument('-s', '--stdout', help='supress all messages except for the encrypted/decrypted output. overrides output-file', action="store_true")
	parser.add_argument('input_file', help='specify input file. If blank %(prog)s will attempt to use stdin.', nargs='?', default=(None if sys.stdin.isatty() else sys.stdin))
	parser.add_argument('-o', '--output-file', help='specify an output file. If not used %(prog)s will generate a filename.', default=None)
	parser.add_argument("-v", "--verbose", help='more verbose output', action="store_true")
	parser.add_argument('--decode', help='switch to decoder. default is encoder', action="store_true")
	parser.add_argument('--overwrite', help='this will overwrite the input file instead of creating a new file', action="store_true")
	parser.add_argument("--debug", help='more output for debugging. --verbose is implied and will print even in --stdout mode', action="store_true")
	parser.add_argument('--version', action='version', version='%(prog)s v1.02')

	argument = parser.parse_args()
	module = argument.module
	decrypt = argument.decode
	input = argument.input_file
	output = argument.output_file
	verbose = argument.verbose
	std_out = argument.stdout
	debug = argument.debug
	overwrite = argument.overwrite
	stdin = False
	vprint = PrintTools.PrintVerbose(verbose).vprint
	alwaysPrint = PrintTools.alwaysPrint

	#Make sure there is input. If not error and print the proper module's --help.
	if input is None:
		alwaysPrint("error: no input detected")
		parser.parse_args(['--help'])
		exit()
	else:
		if input != sys.stdin:
			if not os.path.exists(input):
				print("{} does not exist!".format(input))
				exit()

	# If we are using stdout we should turn off printing.
	if std_out is True:
		output = sys.stdout
		PrintTools.blockPrint()

	# If we are debug then we should print no matter what.
	if debug is True:
		vprint = PrintTools.PrintVerbose(True).vprint
		PrintTools.enablePrint()

	# Show passed arguments in debug mode.
	vprint('verbose ebabled!')
	if debug is True:
		vprint("This is probably only going to be for debugging. Selected Args below!")
		arg_print = "Arguments:\n...\n"
		for arg in vars(argument):
			arg_print = arg_print + '[' + arg + " = " + str(getattr(argument, arg)) + ']\n'
		vprint(arg_print+'...')

	# If output isn't specified we need to make an output file.
	if output is None:
		vprint("no output detected. creating file name")
		if input == sys.stdin:
			if decrypt is True:
				output = ('stdin'+'.plain')
			else:
				output = ('stdin'+'.'+module)
		else:
			if decrypt is True:
				output = (input+'.plain')
			else:
				output = (input+'.'+module)
			if overwrite is True:
				output = input

	# Check if input is stdin
	if input == sys.stdin:
		input_string = input.read()
		input_bytes = (str(input_string)).encode('utf 8')
		vprint("input is --stdin")
		vprint("The --stdin string is {}".format(input_string))
		vprint("The --stdin bytes is {}".format(input_bytes))
		input = input_bytes
		stdin = True
	else:
		vprint("input file is {}".format(input))

	if output == sys.stdout:
		vprint("output is --stdout")
	else:
		vprint("output file is {}".format(output))

	encrypt = Encrypter.Ignition(module, input, output, verbose, stdin, decrypt, overwrite)

	encrypt.baseProcessor()

	if std_out is True:
		encrypt.write_stdout()
	else:
		encrypt.write_file()

if __name__ == "__main__":
	main()