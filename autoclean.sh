#!/bin/sh

if [ -f "Makefile" ]; then
	make distclean
fi

rm -rf Makefile.in aclocal.m4 autom4te.cache/ configure data/Makefile.in \
	data/icons/Makefile.in install-sh missing py-compile \
	src/silver/Makefile.in ABOUT-NLS compile config.guess config.rpath \
	config.sub po/boldquot.sed po/en@boldquot.header po/en@quot.header \
	po/insert-header.sin po/Makefile.in.in po/Makevars.template \
	po/quot.sed po/remove-potcdate.sin po/ru.gmo po/Rules-quot \
	po/silver-rain.pot po/stamp-po m4
