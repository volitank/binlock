# This file is part of binlock.

# binlock is a simple encoding and encryption program.
# Copyright (C) 2021, 2022 Blake Lee

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
"""A simple encoding and encryption program."""
from __future__ import annotations

import argparse
import sys
from typing import NoReturn

from cryptography.exceptions import InvalidTag

from binlock import __version__
from binlock.bintools import (
	GENERATE,
	STDIN,
	STDOUT,
	BinLock,
	CryptoData,
	Log,
	gen_filename,
	get_password,
)


# Overwrite native error and help subclasses
class BinlockParser(argparse.ArgumentParser):
	"""Override argparser for better error."""

	def error(self, message: str) -> NoReturn:
		"""Override argparser for better error."""
		sys.stderr.write(f"error: {message}\n")
		self.print_help()
		sys.exit(1)


def bin_formatter(prog: str) -> argparse.HelpFormatter:
	"""Create the formatter for parser."""
	return argparse.HelpFormatter(prog, max_help_position=64)


def run_binlock() -> None:
	"""Execute binlock."""
	parent_parser = BinlockParser(
		"parent", formatter_class=bin_formatter, add_help=False
	)

	global_option = parent_parser.add_argument_group("global options")

	global_option.add_argument(
		"-h",
		"--help",
		action="help",
		help="show this help message and sys.exit",
	)

	global_option.add_argument(
		"-v",
		"--verbose",
		action="store_true",
		help="more verbose output",
	)

	global_option.add_argument(
		"-i",
		"--input",
		metavar="FILENAME",
		nargs="?",
		default=STDIN,
		help="specify input file. if unused read from stdin.",
	)

	# `binlock -o` Gives GENERATE
	# `binlock -o /filename` gives "/filename"
	# `binlock` gives STDOUT
	global_option.add_argument(
		"-o",
		"--output",
		metavar="FILENAME",
		nargs="?",
		default=STDOUT,
		const=GENERATE,
		help=(
			"specify an output file."
			" If not present, write to stdout."
			" If present with no file name generate a filename."
		),
	)

	global_option.add_argument(
		"--debug",
		action="store_true",
		help="more output for debugging. --verbose is implied.",
	)

	global_option.add_argument(
		"--version",
		action="version",
		version=f"binlock v{__version__}",
	)

	parser = BinlockParser(
		formatter_class=bin_formatter,
		parents=[parent_parser],
		add_help=False,
		usage="binlock [--options] [-e b64, b85, a85] [-i input] [-o output]",
	)

	encoder_option = parser.add_argument_group("encoder options")

	encoder_option.add_argument(
		"-e",
		"--encoder",
		metavar="b64, b85, a85",
		choices=["b64", "b85", "a85"],
		nargs="?",
		default="b64",
		help="choose which encoder to use.",
	)

	encoder_option.add_argument(
		"--decode",
		action="store_true",
		help="switch to decoder. default is encoder",
	)

	subparsers = parser.add_subparsers(
		title="crypt",
		# description='This is the action for encryption and decryption',
		metavar="binlock crypt --help",
		dest="crypt",
		help="print help for the encryption sub module",
	)

	parser_aes = subparsers.add_parser(
		"crypt",
		formatter_class=bin_formatter,
		usage="binlock [crypt] [--options] [-i input] [-o output]",
		add_help=False,
		epilog="binlock crypt currently only supports encryption with password.",
		parents=[parent_parser],
	)

	crypt_option = parser_aes.add_argument_group("crypt options")

	crypt_option.add_argument(
		"--decrypt",
		action="store_true",
		help="switch to decryption. default is encryption",
	)

	crypt_option.add_argument(
		"--dump-header",
		action="store_true",
		help="prints header information and sys.exits",
	)

	config = parser.parse_args()
	log = Log(config.debug, config.verbose)
	# Make sure there is source. If not error and print --help.
	if config.input == STDIN and sys.stdin.isatty():
		# stdin being a tty means that its not piped
		log.err("no input detected")
		parser.parse_args(["--help"])
		sys.exit(1)

	# If verbose or debug is enabled we should print to console.
	log.debug("arguments:")
	for arg in vars(config):
		log.debug(f"[{arg} = {getattr(config, arg)}]")

	# This is where the main program really starts
	if not config.crypt:
		log.fatal("Decryption not yet supported.")
		# The encoder needs some work for the new changes lol
		binlock = BinLock(config.input, gen_filename(config.output, log, config.decode))
		binlock.write_bytes(binlock.encode(config.encoder, config.decode))

	# If it's not encryption mode the code stops here
	binlock = BinLock(
		config.input,
		gen_filename(config, log, config.decrypt),
	)

	crypto = CryptoData()
	if config.dump_header:
		binlock.read_header(crypto)
		print(binlock.dump_header(crypto))
		sys.exit(0)

	if config.decrypt:
		binlock.read_header(crypto)
		while True:
			try:
				crypto.create_key(get_password(log, decrypt=True))
				binlock.write_bytes(binlock.aes_decrypt(crypto))
			except InvalidTag:
				log.fatal("Invalid Tag. Is the password correct?")

	# Nothing matched must be encrypt mode
	crypto.create_key(get_password(log, decrypt=False))

	crypt_data = binlock.aes_encrypt(crypto)
	header = crypto.create_header()

	append_head = header + crypt_data
	binlock.write_bytes(append_head)
