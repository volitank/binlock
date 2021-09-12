#!/usr/bin/env python3

import argparse
import sys
import os
import PrintTools
import Encrypter

# Overwrite native error subclass
class BinlockParser(argparse.ArgumentParser):
	def error(self, message):
		sys.stderr.write('error: %s\n' % message)
		self.print_help()
		sys.exit(2)

def main():
	common = BinlockParser(add_help=False)
	#common.add_argument("-t", "--test", help='switch for testing', action="store_true")
	common.add_argument("-v", "--verbose", help='more verbose output', action="store_true")
	common.add_argument("-d", "--debug", help='more output for debugging. --verbose is implied. Will print even in --stdout mode', action="store_true")

	parser = BinlockParser(parents=[common])

	subparsers = parser.add_subparsers(dest='module', help='[base64|aes] [encrypt|decrypt] [infile] [outfile]', metavar='[encryption_module]', required=True)
	
	common.add_argument("mode", choices=['encrypt', 'decrypt'], metavar='[encrypt|decrypt]', help='[infile] [outfile]')
	common.add_argument('-s', '--stdout', help='supress all messages except for the encrypted/decrypted output.', action="store_true")
	common.add_argument('-i', '--input-file', default=(None if sys.stdin.isatty() else sys.stdin))
	common.add_argument('-o', '--output-file', default=None)

	base65_parser = subparsers.add_parser("base64", parents=[common])
	aes_parser = subparsers.add_parser("aes", parents=[common])

	argument = parser.parse_args()
	module = argument.module
	mode = argument.mode
	input = argument.input_file
	output = argument.output_file
	verbose = argument.verbose
	std_out = argument.stdout
	debug = argument.debug
	stdin = False
	vprint = PrintTools.PrintVerbose(verbose).vprint

	#Make sure there is input. If not error and print the proper module's --help.
	if input is None:
		vprint("error: no input detected")
		if module == 'base64':
			base65_parser.parse_args(['--help'])
		elif module == 'aes':
			aes_parser.parse_args(['--help'])
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

	# FINISH THIS SECTION FOR DEBUGGING.
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
		new_name = (module+'-'+mode)
		if input == sys.stdin and module == 'base64':
			output = (new_name+'.64')
		elif input == sys.stdin and module == 'aes':
			output = (new_name+'.aes')
		else:
			output = (input+'.64')

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
	
	encrypt = Encrypter.Ignition(module, mode, input, output, verbose, stdin)

	encrypt.processor64()

	if std_out is True:
		encrypt.write_stdout()
	else:
		encrypt.write_file()

if __name__ == "__main__":
	main()