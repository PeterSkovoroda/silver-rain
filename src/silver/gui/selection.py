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

from silver.msktz import MSK
from silver.translations import WEEKDAY_LIST

class Selection(Gtk.Box):
    """ Selection buttons """
    def __init__(self, app):
        self._app = app
        self._selection_buttons = []
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL,
                         spacing=0)
        for day in WEEKDAY_LIST:
            button = Gtk.Button(day)
            button.set_focus_on_click(True)
            button.set_size_request(80, 0)
            button.connect("clicked", self._on_clicked)
            self.pack_start(button, True, True, 0)
            self._selection_buttons.append(button)
        self.show_all()

    def selection_update(self):
        """ Select today's section """
        wd = datetime.now(MSK()).weekday()
        self._selection_buttons[wd].clicked()
        Gtk.Widget.grab_focus(self._selection_buttons[wd])

    def _on_clicked(self, button):
        """ Refilter treeview by selected weekday """
        wd = WEEKDAY_LIST.index(button.get_label())
        self._app.refilter(wd)
