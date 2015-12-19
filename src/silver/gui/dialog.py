#!/usr/bin/env python3
"""
Copyright (C) 2015 Petr Skovoroda <petrskovoroda@gmail.com>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public
License along with this program; if not, write to the
Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
Boston, MA 02110-1301 USA
"""

from gi.repository import Gtk
import logging
import textwrap

class Dialog(Gtk.Dialog):
    """ Modal dialog window with message """
    def __init__(self, parent, title, icon, msg):
        Gtk.Dialog.__init__(self)
        self.set_title("Silver Rain: " + title)
        self.set_resizable(False)
        self.set_transient_for(parent)
        # Image
        icontheme = Gtk.IconTheme.get_default()
        pb = icontheme.load_icon(icon, 48, 0)
        img = Gtk.Image()
        img.set_from_pixbuf(pb)
        # Message
        message = textwrap.fill("<b>{0}:</b> {1}".format(title, msg), 50)
        text = Gtk.Label(message)
        text.set_use_markup(True)
        # Pack
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_border_width(10)
        grid.attach(img, 0, 0, 1, 1)
        grid.attach(text, 1, 0, 1, 1)
        box = self.get_content_area()
        box.set_spacing(10)
        box.pack_start(grid, True, True, 0)
        self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.show_all()

def show_dialog(parent, title, icon, msg):
    """ Run dialog """
    dialog = Dialog(parent, title, icon, msg)
    dialog.run()
    dialog.destroy()
