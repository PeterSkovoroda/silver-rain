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

from gi.repository import Gtk, GdkPixbuf

from silver.globals import ICON

class MainWindow(Gtk.Window):
    """ Parent window """
    def __init__(self, menubar, selection, control_panel):
        Gtk.Window.__init__(self, title="Silver Rain")
        self.hidden = True
        self.set_border_width(0)
        self.set_icon_name(ICON)
        self.set_size_request(650, 450)
        self.set_resizable(False)
        self.connect("delete-event", self._on_delete_event)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        # Menubar
        vbox.pack_start(menubar, False, False, 0)
        sep = Gtk.Separator()
        vbox.pack_start(sep, False, False, 0)
        # Set hotkeys
        self.add_accel_group(menubar.accel_group)
        # Scrolled window
        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.set_policy(Gtk.PolicyType.NEVER,
                                         Gtk.PolicyType.AUTOMATIC)
        self._scrolled_window.set_min_content_height(100)
        self._scrolled_window.show()
        # Background
        self._overlay = Gtk.Overlay()
        self._img = Gtk.Image()
        self._img.show()
        self._overlay.add(self._img)
        self._overlay.add_overlay(self._scrolled_window)
        self._overlay.show()
        vbox.pack_start(self._overlay, True, True, 0)
        # Selection
        vbox.pack_start(selection, False, False, 0)
        # Controls
        vbox.pack_end(control_panel, False, False, 0)
        vbox.show()
        self.add(vbox)

    def set_widget(self, widget):
        """ Add widget to sclrolled window """
        self._scrolled_window.add(widget)

    def _on_delete_event(self, window, event):
        """ Hide parent window instead of destroying it """
        self.hidden = True
        window.hide()
        return True

    def set_background(self, file):
        """ Set background image """
        w = self._overlay.get_allocation().width
        h = self._overlay.get_allocation().height
        if not file:
            pb = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, w, h)
            pb.fill(0xffffffff)
        else:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_size(file, w, -1)
        self._img.set_from_pixbuf(pb)
