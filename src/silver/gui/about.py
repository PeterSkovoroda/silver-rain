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
import re
import textwrap

from silver.globals import ICON
from silver.globals import VERSION

class About(Gtk.Dialog):
    """ About dialog """
    def __init__(self, parent):
        Gtk.Dialog.__init__(self)
        self.set_title("Silver Rain: About")
        self.set_transient_for(parent)
        self.set_resizable(False)
        # Header
        header = Gtk.HBox(spacing=5)
        header.set_border_width(0)
        logo = Gtk.Image.new_from_icon_name(ICON, 64)
        logo.set_pixel_size(50)
        title = Gtk.Label()
        title.set_markup("<span size='18000'><b>Silver Rain</b></span>\n" +
                         "<span size='11000'>Version " + VERSION + "</span>")
        title.set_alignment(0, 0)
        title.set_selectable(True)
        header.pack_start(logo, False, False, 0)
        header.pack_start(title, False, False, 0)
        # Text
        s = """Unofficial Silver Rain Radio application for Linux.
        This pruduct is not approved in any way by Silver Rain Radio
        or anybody else."""
        text = Gtk.Label(textwrap.fill(re.sub(r'\s+', r' ', s), 44))
        text.set_selectable(True)
        text.set_justify(Gtk.Justification.CENTER)
        # Copyright
        s = """Check for the latest version
        <a href='https://github.com/petrskovoroda/silver-rain'>here</a>"""
        s = re.sub(r'\s+', r' ', s)
        s += "\n"
        s += "Copyright \xa9 2015 Petr Skovoroda"
        copyright = Gtk.Label()
        copyright.set_markup(s)
        copyright.set_selectable(True)
        copyright.set_justify(Gtk.Justification.CENTER)
        # Link
        s = "<a href='http://silver.ru'>http://silver.ru</a>"
        link = Gtk.Label()
        link.set_markup(s)
        link.set_justify(Gtk.Justification.CENTER)
        # Pack area
        area = self.get_content_area()
        area.set_spacing(10)
        area.set_border_width(10)
        area.pack_start(header, False, False, 0)
        area.pack_start(text, True, True, 0)
        area.pack_start(copyright, True, True, 0)
        area.pack_start(link, True, True, 0)
        self.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        self.show_all()
