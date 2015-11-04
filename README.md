Silver Rain
===========

Silver Rain radio application for Linux
* Official website: http://silver.ru

### Features
* TBD

License
-------
This program is free software; you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not,
write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
USA.

Dependencies
------------
* Python 3
* GStreamer 1.0
* GStreamer 1.0 plugins base
* GStreamer 1.0 plugins good
* GStreamer 1.0 plugins ugly
* GTK+3

Installation
------------
### Ubuntu
TBD

### Compiling from source using autotools

Get the code:

    git clone https://github.com/petrskovoroda/silver-rain.git && cd silver-rain

Compile and install:

    ./autogen.sh --prefix=/usr
    make
    sudo make install
