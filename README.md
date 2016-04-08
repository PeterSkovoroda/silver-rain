Silver-rain
===========

Unofficial [Silver Rain] (http://silver.ru) radio application for Linux  
Неофициальное приложение радиостанции [Серебряный Дождь] (http://silver.ru) для Linux

### Features / Функции
* Listen live  
  Слушать онлайн
* Browse schedule  
  Просматривать сетку вещания
* Record your favorite programms  
  Записывать любимые программы
* Send messages to the studio  
  Отправлять сообщения в студию

License / Лицензия
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

Dependencies / Зависимости
------------
* Python 3
* python3-gobject python3-requests python3-requests
* GStreamer 1.0
* GStreamer 1.0 plugins base, good, ugly
* GTK+3  
* gnome-icon-theme (Fedora/OpenSuSE)

Installation / Установка
------------

### Compiling from source using autotools

    ./autogen.sh --prefix=/usr
    make
    sudo make install
