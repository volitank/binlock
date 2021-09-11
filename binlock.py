#!/usr/bin/env python3
#TODO
#Implement AES encryption
#Make Verbosity and printing better

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
    common.add_argument("-v", "--verbose", help='test more verbose output', action="store_true")
    
    parser = BinlockParser(parents=[common])

    subparsers = parser.add_subparsers(dest='module', help='[base64|aes] [encrypt|decrypt] [infile] [outfile]', metavar='[encryption_module]', required=True)
    
    common.add_argument("mode", choices=['encrypt', 'decrypt'], metavar='[encrypt|decrypt]', help='[infile] [outfile]')
    common.add_argument('-s', '--stdout', help='supress all messages except for the encrypted/decrypted output.', action="store_true")
    common.add_argument('-S', '--stdout-print', help="use with --stdout to print messages to console for debugging.", action="store_true")
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
    std_out_print = argument.stdout_print
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

    if std_out is True:
        output = sys.stdout
        PrintTools.blockPrint()
        if std_out_print is True:
            PrintTools.enablePrint()
    
    vprint('verbose ebabled!')

    #if output isn't specified we need to make an output file.
    if output is None:
        vprint("no output detected. creating file name")
        new_name = (module+'-'+mode)
        if input == sys.stdin and module == 'base64':
            output = (new_name+'.64')
        elif input == sys.stdin and module == 'aes':
            output = (new_name+'.aes')
        else:
            output = (input+'.64')

    if input == sys.stdin:
        vprint("input is --stdin")
    else:
        vprint("input is {}".format(input))

    if output == sys.stdout:
        vprint("output is --stdout")
    else:
        vprint("output is {}".format(output))

    # vprint("This is probably only going to be for debugging. Selected Args below!")
    # for arg in vars(argument):
    #     vprint((arg, getattr(argument, arg)))
    vprint("This is probably only going to be for debugging. Selected Args below!")
    for arg in vars(argument):
        vprint((arg+' = '+str(getattr(argument, arg))))
    vprint('')
    
    Encrypter.Ignition(module, mode, input, output, verbose).processor64()

if __name__ == "__main__":
    main()