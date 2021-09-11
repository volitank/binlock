#!/bin/bash
## Run this in the same directory as 
## binlock to test functionality.

echo "#################################"
echo "#binlock development test script#"
echo "#################################"
echo ""
echo "#################################"
echo "##starting the encryption tests##"
echo "#################################"
echo ""
# use stdin and make and generate an output file
echo "Our input for encryption is:"
echo "This is a fresh testing string"
echo "This is a fresh testing string" | ./binlock.py base64 encrypt

#echo the same string into a file
echo "This is a fresh testing string" > test.file.plain

echo""
echo "This is what our encryption string is."
# Encrypt the test file and send it to stdout
./binlock.py base64 encrypt -i test.file.plain -s
echo ""
# Then do the same thing but redirect it to a file
./binlock.py base64 encrypt -i test.file.plain -s > test.file.64.stdout
echo""
# Let us encrypt the test file generating new name test.file.plain.64
./binlock.py base64 encrypt -i test.file.plain 

#Finally for encryption we will specify an output file
./binlock.py base64 encrypt -i test.file.plain -o test.file.plain.64.output

#compare the test file and the stdout file. they should be the same
sha256sum test.file.plain.64 test.file.64.stdout base64-encrypt.64 test.file.plain.64 test.file.plain.64.output
echo ""
echo "#################################"
echo "####encryption test complete#####"
echo "####verify all the hashes match##"
echo "#################################"
echo ""
echo "#################################"
echo "####starting the decrypt test####"
echo "#################################"
echo ""
echo "output string should match the input string"


########STOP if there is any differences or any bugs
#############we should try to fix them and restart

#let us make sure we can get the same starting files.
#First use stdin and print to console
cat base64-encrypt.64 | ./binlock.py base64 decrypt -s

echo ""

#now do the same thing but redirecting to a file.
cat base64-encrypt.64 | ./binlock.py base64 decrypt -s > base64-encrypt.64.stdout

#next check stdin and then have it generate an output file base64-decrypt.64
cat base64-encrypt.64 | ./binlock.py base64 decrypt

#Do the same exact thing but file to file
./binlock.py base64 decrypt -i base64-encrypt.64 -o base64-encrypt.64.decrypt

#let's try file to stdout
./binlock.py base64 decrypt -i base64-encrypt.64 -s > base64-encrypt.64.stdout-2

#finally let's do stdin to a file
cat base64-encrypt.64 | ./binlock.py base64 decrypt -o base64-encrypt.64.stdin-file

sha256sum test.file.plain base64-encrypt.64.stdout base64-decrypt.64 base64-encrypt.64.stdout-2 base64-encrypt.64.stdin-file base64-encrypt.64.decrypt

