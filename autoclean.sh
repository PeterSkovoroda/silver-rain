#!/bin/sh

if [ -f "Makefile" ]; then
	make distclean
fi

rm -rf Makefile.in aclocal.m4 autom4te.cache/ configure data/Makefile.in \
	data/icons/Makefile.in install-sh missing py-compile src/silver/Makefile.in
