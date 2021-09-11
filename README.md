# binlock

A simple encoder program for base64.

# TODO

- Implement aes encryption.

	>Make a switch to encrypt the entire filesystem.
	>Make a switch to throw away the aes key.
- Allow multiple input files.
	>Multiple inputs to multiple outputs?
	>Multiple inputs to a single output?
- Allow executing encrypted binaries?
- Double encode switch
- Implement different encoders
- Of course we always need to look at making the code better.

# Usage
All you have to do is have python3 installed and run ./binlock.py -h and it will instruct you. I may make binaries for it if it grows.

# exit()
I will definitley add to this as we go. There isn't much reason for Encrypter and PrintTools to be different files I just wanted it that way. The same reason that all my encoder functionality is in a class.
