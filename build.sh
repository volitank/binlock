#!/bin/bash

# Define variables
ver=1.04
winver=0.1.0.4
rev=-1
arch=amd64
deb_path="deb/binlock_$ver${rev}_$arch"
user=$(whoami)

confirm () {
	while :
	do
		read -r -p "$1 [y/N] " response
		response=${response,,}
		if [[ "$response" =~ ^(yes|y)$ ]]
		then
			printf "\nconfirmed\n"
			return 0
		elif [[ "$response" =~ ^(no|n)$ ]]
		then
			printf "\nyou've declined\n"
			return 1
		else
			printf "\nnot a valid choice\n"
		fi
	done
}

finished () {
    echo "all finished enjoy your new build"
    echo "log file: /tmp/binlock_$ver${rev}_$arch.build"
    echo "binaries are located in the release directory"
    exit 0
}

# Make a build directory if it doesn't exist and enter it.
mkdir build > /dev/null && echo "created build directory"

cd build || { echo "error: unable to change into build directory" ; exit 1; }

# Create our release directory
mkdir ../release && echo "created release"

# Build linux binary
echo "building linux binary..."
#cp ../binlock.py ../Encoder.py ./
if nuitka3 --follow-imports --assume-yes-for-downloads ../binlock.py -o binlock > /tmp/binlock_$ver${rev}_$arch.build 2>&1 ; then
    echo "linux binary built"
else
    echo "building linux binary failed"
    echo "please check the log file: /tmp/binlock_$ver${rev}_$arch.build"
	exit 1
fi

# Build AppImage
echo "building AppImage... this might take a minute..."
if nuitka3 --onefile --assume-yes-for-downloads --linux-onefile-icon=../icon/binlock.png --output-dir=./AppImage ../binlock.py >> /tmp/binlock_$ver${rev}_$arch.build 2>&1 ; then
    echo "AppImage Built"
else
    echo "building AppImage failed"
    echo "please check the log file: /tmp/binlock_$ver${rev}_$arch.build"
	exit 1
fi

if cp ./AppImage/binlock.bin ../release/binlock_$ver${rev}_$arch.AppImage >> /tmp/binlock_$ver${rev}_$arch.build 2>&1 ; then
    echo "AppImage copied to Release directory as binlock_$ver${rev}_$arch.AppImage"
else
    echo "error: copying AppImage didn't work"
    echo "please check the log file: /tmp/binlock_$ver${rev}_$arch.build"
	exit 1
fi

# Build deb package

# Make our directory
echo "making $deb_path/usr/bin/ directory"
mkdir -p $deb_path/usr/bin/
echo "making $deb_path/DEBIAN/ directory"
mkdir -p $deb_path/DEBIAN/

# Copy the binary
if cp ./binlock $deb_path/usr/bin/binlock > /dev/null ; then
    echo "copy binlock to $deb_path/usr/bin/binlock successful"
else
    echo "unable to copy binlock"
	exit 1
fi

# build our debian control file
if {
echo "Package: binlock";
echo "Version: $ver";
echo "Architecture: $arch";
echo "Maintainer: Blake <blake@volitank.com>";
echo "Description: A simple encoder for base64, base85 and ascii85.";
echo "Depends: libc6 (>= 2.29), libpython3.9 (>= 3.9.1)"
} > $deb_path/DEBIAN/control ; then
    echo "created $deb_path/DEBIAN/control"
else
    echo "failed to create $deb_path/DEBIAN/control"
	exit 1
fi

# We need to cd into deb
echo "building binlock_$ver${rev}_$arch.deb"
cd deb || { echo "unable to change directory" ; exit 1; }
if dpkg-deb --build --root-owner-group binlock_$ver${rev}_$arch >> /tmp/binlock_$ver${rev}_$arch.build 2>&1 ; then
    echo "binlock_$ver${rev}_$arch.deb created successfully"
else
    echo "failure creating binlock_$ver${rev}_$arch.deb"
    echo "please check the log file: /tmp/binlock_$ver${rev}_$arch.build"
	exit 1
fi
cd .. || { echo "unable to change directory" ; exit 1; }

if cp deb/binlock_$ver${rev}_$arch.deb ../release/ > /dev/null ; then
    echo "binlock_$ver${rev}_$arch.deb copied to Release directory"
else
    echo "failure copying binlock_$ver${rev}_$arch.deb"
	exit 1
fi

# Building a snap
# Create our snap directory
cp -r ../icon/ ./icon || echo "snap building is likely to fail due to missing icon"

mkdir snap && echo "created snap directory"
if {
echo "name: binlock"
echo "version: '$ver$rev'"
echo "summary: Cross-Platform Encoder"
echo "description: |"
echo "  binlock is a program that encodes or decodes base64, base85 or ascii85."
echo "grade: stable"
# [devel, stable, candidate]
echo "confinement: classic"
#echo "confinement: strict"
# [strict, devmode, classic]
echo "base: core20"
# [core18, core20]
echo "compression: lzo"
# [xz, lzo]
echo "icon: ./icon/binlock-snap.png"
echo ""
echo "passthrough:"
echo "  license: GPL-3.0-or-later"
echo ""
echo "parts:"
echo "  binlock:"
echo "    plugin: dump"
      #    source: ./binlock-snap_1.03-1_amd64.tar.gz
      #    source-type: tar
echo "    source: deb/binlock_$ver${rev}_$arch.deb"
echo "    source-type: deb"
echo "    stage-packages: [libpython3.9]"
echo ""
echo "apps:"
echo "  binlock:"
echo "    command: usr/bin/binlock"
#echo "    plugs:"
#echo "        - home"
#echo "        - removable-media"
echo "    environment:"
echo '        PYTHONPATH: $SNAP/lib/x86_64-linux-gnu/:$SNAP/usr/lib/python3.9/:$PYTHONPATH'
echo '        PYTHONHOME: $SNAP/lib/x86_64-linux-gnu/:$SNAP/usr/lib/python3.9/:$PYTHONHOME'
} > snap/snapcraft.yaml ; then
    echo "created snapcraft.yaml"
else
    echo "unable to create snapcraft.yml"
	exit 1
fi

# Make sure we're clean
echo "making sure snap is clean.."
snapcraft clean >> /tmp/binlock_$ver${rev}_$arch.build 2>&1

# Now we can build
echo "starting automated snap build. This can take a VERY long time.."
if snapcraft >> /tmp/binlock_$ver${rev}_$arch.build 2>&1 ; then
    echo "successfully built snap"
else
    echo "unable to build snap"
	echo "please check the log file: /tmp/binlock_$ver${rev}_$arch.build"
	exit 1
fi

cp ./binlock_$ver${rev}_$arch.snap ../release/
echo "copied binlock_$ver${rev}_$arch.snap to release directory"


if confirm "do you want to build for windows? You'll need sudo.." ; then
    ## Windows build ##
    # Make our chroot directory
    sudo mkdir binlock_$ver${rev}_$arch-chroot
    # Make double sure that it is owned by root
    sudo chown root:root binlock_$ver${rev}_$arch-chroot
    # If our tar.gz doesn't exist we need to get it.
    if find binlock-chroot.tar.gz ; then
        echo "binlock-chroot.tar.gz exists"
    else
        echo "binlock-chroot.tar.gz not found. Downloading.."
        wget https://github.com/volitank/binlock/releases/download/v1.03/binlock-chroot.tar.gz -q --show-progress --progress=bar:force 2>&1 | tee -a /tmp/binlock_$ver${rev}_$arch.build || { echo "unable to download binlock-chroot.tar.gz" ; exit 1; }
        echo "binlock-chroot.tar.gz downloaded successfully"
    fi
    # Extract our build environment
    echo "unpacking windows build environment.."
    if sudo tar -xvf ./binlock-chroot.tar.gz --directory=binlock_$ver${rev}_$arch-chroot >> /tmp/binlock_$ver${rev}_$arch.build 2>&1 ; then
        echo "build environment unpacked successfully"
    else
        echo "please check the log file: /tmp/binlock_$ver${rev}_$arch.build"
        exit 1
    fi

    # Start copying some files into the environment
    sudo cp ../*.py binlock_$ver${rev}_$arch-chroot/root/
    sudo cp -R ../icon binlock_$ver${rev}_$arch-chroot/root/

    # Start our build with wine
    echo "starting windows builds.. this could take a while.."
    if sudo chroot binlock_$ver${rev}_$arch-chroot /bin/bash -c \
    "wine /root/Python/python -m nuitka \
    --assume-yes-for-downloads \
    --onefile \
    --windows-product-version=$winver \
    --windows-file-version=$winver \
    --windows-product-name=binlock \
    --windows-company-name=volitank \
    --windows-icon-from-ico=/root/icon/binlock.png \
    --windows-file-description=\"A simple encoder for base64, base85 and ascii85\" /root/binlock.py; \

    wine /root/Python/python -m nuitka \
    --assume-yes-for-downloads \
    --standalone \
    --windows-product-version=$winver \
    --windows-file-version=$winver \
    --windows-product-name=binlock \
    --windows-company-name=volitank \
    --windows-icon-from-ico=/root/icon/binlock.png \
    --windows-file-description=\"A simple encoder for base64, base85 and ascii85\" /root/binlock.py" |& cat >> /tmp/binlock_$ver${rev}_$arch.build ; then
        echo "windows builds successful"
    else
        echo "please check the log file: /tmp/binlock_$ver${rev}_$arch.build"
        exit 1
    fi

    # Copy our onefile
    if sudo cp binlock_$ver${rev}_$arch-chroot/binlock.exe ../release/binlock_$ver${rev}_$arch-onefile.exe ; then
        echo "release/binlock_$ver${rev}_$arch-onefile.exe copied successfully"
    else
        echo "copying release/binlock_$ver${rev}_$arch-onefile.exe failed"
    fi

    # Zip up ourfiles
    if sudo zip -j ../release/binlock_$ver${rev}_$arch.zip binlock_$ver${rev}_$arch-chroot/binlock.dist/binlock.exe \
    binlock_$ver${rev}_$arch-chroot/binlock.dist/python39.dll \
    binlock_$ver${rev}_$arch-chroot/binlock.dist/vcruntime140.dll >> /tmp/binlock_$ver${rev}_$arch.build ; then
        echo "release/binlock_$ver${rev}_$arch.zip create successfully"
    else
        echo "error creating release/binlock_$ver${rev}_$arch.zip"
        exit 1
    fi

    sudo chown "$user": ../release/binlock_$ver${rev}_$arch-onefile.exe || echo "unable to set correct permissions on release/binlock_$ver${rev}_$arch-onefile.exe"
    sudo chown "$user": ../release/binlock_$ver${rev}_$arch.zip || echo "unable to set correct permissions on release/binlock_$ver${rev}_$arch.zip"
    echo "copied binlock_$ver${rev}_$arch-onefile.exe"
    echo "binlock_$ver${rev}_$arch.zip to release directory"
    cd .. || { "dammit we exited so soon :(" ; exit 1; }

    if confirm "Would you like to clean up the build directory?" ; then
        echo "cleaning up the build directory..."
        sudo rm -rf build/ || { "error removing the build directory" ; exit 1; }
    else
        if confirm "Would you like to clean up the chroot?" ; then
            echo "cleaning up the chroot.."
            sudo rm -rf build/binlock_$ver${rev}_$arch-chroot/ || { "error removing the chroot" ; exit 1; }
            finished
        else
            finished
        fi
    fi

else
    echo "not building windows"
    cd .. || { "dammit we exited so soon :(" ; exit 1; }
    if confirm "Would you like to clean up the build directory?" ; then
        echo "cleaning up the build directory..."
        rm -rf build/ || { "error removing the build directory" ; exit 1; }
    else
        finished
    fi

fi

finished
