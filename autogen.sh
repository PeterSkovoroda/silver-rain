#!/bin/sh

if [ $(which ggnome-autogen.sh) ]; then
	srcdir=`dirname $0`
	$srcdir gnome-autogen.sh $@
else
	aclocal
	autoconf
	automake --add-missing
	./configure $@
	echo "Now run 'make && make install'"
fi
