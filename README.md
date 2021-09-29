# binlock

  

A simple encoder program for base64, base85 and ascii85.

  

# TODO

- Implement aes encryption.

>Make a switch to encrypt the entire filesystem.

>Make a switch to throw away the aes key.

- Allow multiple input files.

>Multiple inputs to multiple outputs?

>Multiple inputs to a single output?

- Allow executing encrypted binaries?

- Double encode switch

- Of course we always need to look at making the code better.

  

# Usage

  

**Python**

>Make sure you have python3 installed.

`git clone https://github.com/volitank/binlock.git`
>or just download `binlock.py` and `encoder.py`. You don't need the rest

`python3 binlock.py --help` or

`/path/to/binlock.py --help` or

`./binlock.py --help`

**.deb:**

`sudo dpkg -i binlock_ver-rev_arch.deb`

`binlock --help`

**AppImage:**

`./binlock_ver-rev_arch.AppImage --help`

**Windows:**

>For Windows you can use the portable onefile.

`binlock_ver-rev_arch-onefile.exe --help`

>Other option is get the zip file and extract it.

`binlock.exe --help`

**Snap**
>I don't have the snap on the snap store yet, It needs to be approved. For now I am distributing a --classic snap here.

`sudo snap install binlock_ver-rev_arch.snap --classic --dangerous`

`binlock --help`

All binaries compiled with nuitka3