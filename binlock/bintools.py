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
import hashlib
import json
import logging
import sys
from base64 import a85decode, a85encode, b64decode, b64encode, b85decode, b85encode
from binascii import Error
from getpass import getpass
from os import urandom
from pathlib import Path
from typing import Any, BinaryIO, NoReturn, cast

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from binlock import __version__

eprint = logging.error
vprint = logging.info
dprint = logging.debug

STDIN = "stdin"
STDOUT = "stdout"
GENERATE = "generate"


def _encode(module: str, decode: bool, data: bytes) -> bytes:
	"""Select the correct base to encode."""
	if module == "a85":
		return a85decode(data) if decode else a85encode(data)
	if module == "b64":
		return b64decode(data) if decode else b64encode(data)
	if module == "b85":
		return b85decode(data) if decode else b85encode(data)
	eprint(f"module {module} isn't valid")
	sys.exit(1)


# Encoding and Decoding function


# Asks user for a password
def get_password(log: Log, decrypt: bool) -> bytes:
	"""Ask user for password, confirm it and return it as bytes."""
	while True:
		password = getpass("password:").encode()
		if decrypt:
			return password

		if password == getpass("confirm password:").encode():
			log.verbose("passwords match")
			return password

		del password
		log.err("passwords don't match! try again.")


def open_buffer(
	buffer: str,
	read_only: bool,
	_input: bool,
) -> tuple[BinaryIO, str]:
	"""Open a buffer from either stdio or a Path.

	read_only only will set the file to only be read.
	This has no effect on stdio

	_input as True returns "stdin". False "stdout".
	This has no effect for Paths. The filename is returned.
	"""
	if buffer == STDIN:
		return sys.stdin.buffer, STDIN
	if buffer == STDOUT:
		return sys.stdout.buffer, STDOUT

	# Buffer must be a file name.
	try:
		path = Path(buffer)
		if not _input:
			# Create the out file if it doesn't exist
			path.touch(exist_ok=True)
		return cast(BinaryIO, path.open("rb" if read_only else "wb")), f"{path}"
	except FileNotFoundError:
		sys.exit(f"File {path} does not exist!")


def gen_filename(config: argparse.Namespace, log: Log, decrypt: bool) -> str:
	"""Generate the output filename if necessary."""
	if config.output == GENERATE:
		file_extension = "aes" if config.crypt else config.encoder
		if decrypt:
			file_extension = "plain"

		log.verbose("no output detected. creating file name")
		return f"{config.input}.{file_extension}"
	return cast(str, config.output)


class Log:
	"""Class for Standard I/O."""

	def __init__(self, debug: bool, verbose: bool) -> None:
		"""Class for Standard I/O."""
		self._debug = debug
		self._verbose = verbose

	def verbose(self, msg: object) -> None:
		"""Print message if verbose."""
		if self.debug(msg):
			return

		if self._verbose:
			print(msg)

	def debug(self, msg: object) -> bool:
		"""Print message if debugging."""
		if not self._debug:
			return False
		print(f"DEBUG: {msg}")
		return True

	@staticmethod
	def err(*args: Any, **kwargs: Any) -> None:
		"""Print message to stderr."""
		print(*("Error:", *args), file=sys.stderr, **kwargs)

	@staticmethod
	def fatal(msg: object) -> None:
		"""Print message to stderr and exit the program."""
		sys.exit(f"Error: {msg}")


class CryptoData:
	"""Class to contain cryptographic data."""

	def __init__(self) -> None:
		"""Class to contain cryptographic data."""
		self.key: bytes = b""
		self.data: dict[str, bytes] = {
			"binlock": __version__.encode(),
			"salt": urandom(32),
			"iv": urandom(16),
			"aad": urandom(16),
			"tag": b"",
		}

	def create_key(self, password: bytes) -> None:
		"""Create the encryption key from a password and salt.

		This method uses pbkdf2_hmac with sha512.

		Luks2 default is to use Argon2
		"""
		self.key = hashlib.pbkdf2_hmac(
			# Luks default is sha256
			"sha512",
			# User Password
			password,
			# Random Data
			self.salt,
			# Iterations. Luks default is 2000
			4096,
			# Desired bit-length of the derived key
			32,
		)

	def create_header(self) -> bytes:
		"""Format and pads the binlock header.

		Returns a bytes object that you will append to data.
		"""
		jheader = json.dumps(self.hex()).encode()

		if len(jheader) < 512:
			pad = 512 - len(jheader)
			# Return the finished padded header
			# Potential bug size here for if the header aome how
			# is exactly 512 it will append \x00 and be larger
			return jheader + b"\x00" * pad
		# This whole thing is kind of wack and needs rethunk
		return jheader

	def hex(self) -> dict[str, str]:
		"""Return the stat of crypt data as a hex dict.

		This will only include header information.
		"""
		return {key: value.hex() for key, value in self.data.items()}

	@property
	def version(self) -> bytes:
		"""Get version."""
		return self.data["binlock"]

	@property
	def salt(self) -> bytes:
		"""Get salt."""
		return self.data["salt"]

	@salt.setter
	def salt(self, value: bytes) -> None:
		"""Set salt."""
		self.data["salt"] = value

	@property
	def iv(self) -> bytes:
		"""Get iv."""
		return self.data["iv"]

	@iv.setter
	def iv(self, value: bytes) -> None:
		"""Set iv."""
		self.data["iv"] = value

	@property
	def aad(self) -> bytes:
		"""Get aad."""
		return self.data["aad"]

	@aad.setter
	def aad(self, value: bytes) -> None:
		"""Set aad."""
		self.data["aad"] = value

	@property
	def tag(self) -> bytes:
		"""Get tag."""
		return self.data["tag"]

	@tag.setter
	def tag(self, value: bytes) -> None:
		"""Set tag."""
		self.data["tag"] = value


class BinLock:
	"""Class Binlock."""

	def __init__(
		self,
		input: str,
		output: str,
	) -> None:
		"""Class Binlock."""
		self.input, self.in_file = open_buffer(
			input,
			read_only=True,
			_input=True,
		)

		self.output, self.out_file = open_buffer(
			output,
			read_only=False,
			_input=False,
		)
		self.header_bytes: bytes = b""

	def read_header(self, crypto: CryptoData) -> None:
		"""Return header dict from json.

		If the source header can't be read it errors
		"""
		try:
			self.header_bytes = self.input.read(512).replace(b"\x00", b"")
			header = cast(dict[str, str], json.loads(self.header_bytes))
			if not header.get("binlock"):
				raise json.JSONDecodeError("", "", 0)
		except json.JSONDecodeError:
			sys.exit(f"'{self.in_file}' is not a valid binlock file")

		# Convert header contents into bytes
		for key in {"binlock", "salt", "aad", "iv", "tag"}:
			if not (key_str := header.get(key)):
				sys.exit(f"Header appears to be corrupted. Missing {key}")
			crypto.data[key] = bytes.fromhex(key_str)

	def dump_header(self, crypto: CryptoData) -> str:
		"""Return the header information as a string."""
		out = "Binlock header information:\n\n" f"[File = {self.in_file}]\n"
		for name, value in crypto.hex().items():
			out += f"[{name} = {value}]\n"
		return out

	# AES Encryption function
	def aes_encrypt(self, crypto: CryptoData) -> bytes:
		"""Encrypt source with key, iv and aad.

		source: Should be bytes.
		key: Only 128, 192, and 256 bit keys (16, 32, 64 bytes).
		iv: Initialization_Vector(IV); must be between 8 and 128 bytes (64 and 1024 bits).
		aad: Authenticate Additional Data; must be between 8 and 128 bytes (64 and 1024 bits).

		Returns encrypted data and the Authentication Tag (needed to decrypt)

		Authentication Tag
		A cryptographic checksum on data that is designed to reveal both
		accidental errors and the intentional modification of the data.

		XTS either 256 or 512 = tweak(IV) must be 128-bits (16 bytes)

		you can use the same input for key, iv and aad but it's not recommended.
		"""
		cipher = Cipher(algorithms.AES(crypto.key), modes.GCM(crypto.iv))
		encryptor = cipher.encryptor()
		encryptor.authenticate_additional_data(crypto.aad)

		data = encryptor.update(self.input.read()) + encryptor.finalize()
		crypto.tag = encryptor.tag
		return data

	# AED Decryption function.
	def aes_decrypt(self, crypto: CryptoData) -> bytes:
		"""Decrypt source with key, iv and aad.

		source: Should be bytes.
		key: Only 128, 192, and 256 bit keys (16, 32, 64 bytes).
		iv: Initialization_Vector(IV); must be between 8 and 128 bytes (64 and 1024 bits).
		aad: Authenticate Additional Data; must be between 8 and 128 bytes (64 and 1024 bits).
		tag: This was returned from the encryption process

		Realistically this information will be pulled from the binlock header.

		Functionality for plain crypto without headers will be implemented eventually.
		"""
		# Tag must be at least 16 bytes
		cipher = Cipher(algorithms.AES(crypto.key), modes.GCM(crypto.iv, crypto.tag))
		decryptor = cipher.decryptor()
		decryptor.authenticate_additional_data(crypto.aad)
		return decryptor.update(self.input.read()) + decryptor.finalize()

	def encode(self, module: str = "b64", decode: bool = False) -> bytes:
		"""Encode and Decode input. Returns bytes.

		source: The source whether '/path/to/filename', sys.stdin, or even a simple string
		module: The module to encode with [b64, b85, a85]
		decode: Set to True to switch to decoding

		encode('/path/to/filename.txt', decode=True)

		"This will encode your file to base64"
		"""
		try:
			data = self.input.read()

			if module == "a85":
				return a85decode(data) if decode else a85encode(data)
			if module == "b64":
				return b64decode(data) if decode else b64encode(data)
			if module == "b85":
				return b85decode(data) if decode else b85encode(data)
			sys.exit(f"module {module} isn't valid")
		except (Error, ValueError):
			sys.exit(
				"did you mean to use the encrypt mode?"
				" are you using the proper encoder?"
			)
		except PermissionError as error:
			sys.exit(f"{error}".replace("[Errno 13]", "").lstrip(" "))

	def write_bytes(self, data: bytes) -> NoReturn:
		"""Write bytes to output."""
		try:
			self.output.write(data)
			sys.exit(1)
		except (Error, ValueError) as error:
			sys.exit(
				f"{error}\ndid you mean to use the encrypt mode? are you using the proper encoder?"
			)
		except PermissionError as error:
			sys.exit(f"{error}".replace("[Errno 13]", "").lstrip(" "))
