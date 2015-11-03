#!/bin/sh

if [ $(which gnome-autogen.sh) ]; then
	srcdir=`dirname $0`
	$srcdir gnome-autogen.sh $@
else
	autoreconf --install
	./configure $@
	echo "Now run 'make && make install'"
fi
