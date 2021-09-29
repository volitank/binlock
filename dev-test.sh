#!/bin/bash
## Run this in the same directory as 
## binlock to test functionality.

mkdir test
cd test || exit

encode_test () {
    echo "#################################"
    echo "##starting the encryption tests##"
    echo "#################################"
    echo ""
    echo "Our input for encryption is:"
    echo "This is a fresh testing string"

    # use stdin and make and generate an output file
    echo "This is a fresh testing string" | ../binlock.py -e "$1" -o # stdin.64

    # echo the same string into a file
    echo "This is a fresh testing string" > test.file.plain # test.file.plain

    echo ""
    echo "This is what our encryption string is."
    # Encrypt the test file and send it to stdout
    ../binlock.py -e "$1" -i test.file.plain

    echo ""
    # Then do the same thing but redirect it to a file
    ../binlock.py -e "$1" -i test.file.plain > test.file."$1".stdout
    echo""
    # Let us encrypt the test file generating new name test.file.plain.$1
    ../binlock.py -e "$1" -i test.file.plain -o

    #Finally for encryption we will specify an output file
    ../binlock.py -e "$1" -i test.file.plain -o test.file.plain."$1".output

    #compare the test file and the stdout file. they should be the same
    sha256sum test.file.plain."$1" test.file."$1".stdout stdin."$1" test.file."$1".stdout test.file.plain."$1".output
    echo ""
    echo "#################################"
    echo "####encryption test complete#####"
    echo "####verify all the hashes match##"
    echo "#################################"
    echo ""
}

decode_test() {

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
    ../binlock.py -e "$1" --decode < stdin."$1"

    echo ""

    #now do the same thing but redirecting to a file.
    ../binlock.py --decode -e "$1" > stdin."$1".stdout < stdin."$1"

    #next check stdin and then have it generate an output file stdin.plain
    ../binlock.py --decode -e "$1" -o < stdin."$1"

    #Do the same exact thing but file to file
    ../binlock.py --decode -e "$1" -i stdin."$1" -o stdin."$1".decode

    #let's try file to stdout
    ../binlock.py --decode -e "$1" -i stdin."$1" > stdin."$1".stdout-2

    #finally let's do stdin to a file
    ../binlock.py --decode -e "$1" -o stdin."$1".stdin-file < stdin."$1"

    sha256sum test.file.plain stdin."$1".stdout stdin.plain stdin."$1".decode stdin."$1".stdout-2 stdin."$1".stdin-file
}

echo "#################################"
echo "#binlock development test script#"
echo "#################################"
echo ""

encode_test b64
sleep 2

decode_test b64
sleep 2

encode_test b85
sleep 2

decode_test b85
sleep 2

encode_test a85
sleep 2

decode_test a85
echo ""
echo "Testing --overwrite switch"
echo "../binlock.py -i test.file.plain.b64 --overwrite --decode"
echo ""
echo "Reading test.file.plain.b64:  $(cat test.file.plain.b64)"
../binlock.py -i test.file.plain.b64 --overwrite --decode 
echo "Reading test.file.plain.b64:  $(cat test.file.plain.b64)"