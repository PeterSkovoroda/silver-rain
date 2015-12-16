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

from datetime import datetime
import subprocess

from gi.repository import Gtk, GdkPixbuf

import silver.config as config
from silver.gui.common import create_menuitem
from silver.msktz import MSK
from silver.schedule import SCHED_WEEKDAY_LIST
from silver.translations import _

class SchedTree(Gtk.TreeView):
    def __init__(self, sched):
        Gtk.TreeView.__init__(self)
        self.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        self.connect('button-release-event', self._on_button_release_event)

        self._weekday_filter = datetime.now(MSK()).strftime("%A")
        self._cell_bg_old = ''
        self._cell_fg_old = ''
        self._sched = sched
        # Init model
        self._init_model()
        # Icon
        renderer = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn(" ", renderer, pixbuf=6)
        renderer.set_alignment(1, 0.5)
        self.append_column(column)

        renderer = Gtk.CellRendererText()
        renderer.set_padding(10, 0)
        renderer.set_alignment(0.5, 0.5)
        renderer.set_property('height', 50)
        # Time
        column = Gtk.TreeViewColumn(_("Time"), renderer, text=2, background=7,
                                    foreground=8, font=9)
        column.set_alignment(0.5)
        column.set_min_width(10)
        self.append_column(column)
        # Title
        renderer.set_alignment(0, 0.5)
        renderer.set_property("wrap_mode", Gtk.WrapMode.WORD)
        renderer.set_property("wrap_width", 200)
        column = Gtk.TreeViewColumn(_("Title"), renderer, text=3, background=7,
                                    foreground=8, font=9)
        column.set_alignment(0.5)
        column.set_min_width(50)
        column.set_resizable(True)
        self.append_column(column)
        # Host
        column = Gtk.TreeViewColumn(_("Host"), renderer, text=5, background=7,
                                    foreground=8, font=9)
        column.set_alignment(0.5)
        column.set_min_width(50)
        column.set_resizable(True)
        self.append_column(column)

    def refilter(self, wd):
        """ Refilter TreeView """
        self._weekday_filter = SCHED_WEEKDAY_LIST[wd]
        self._model.refilter()

    def reset_current(self):
        """ Reset currently marked row """
        if not self._cell_bg_old:
            # Nothing to reset
            return
        # Get current position
        pos = self._sched.get_event_position()
        path = Gtk.TreePath(pos)
        iter = self._model.get_iter(path)
        # Set old colors and font
        self._model[iter][7] = self._cell_bg_old
        self._model[iter][8] = self._cell_fg_old
        self._model[iter][9] = config.font
        # Delete backup
        self._cell_bg_old = ''
        self._cell_fg_old = ''

    def mark_current(self):
        """ Set current event colors """
        # Get current position
        pos = self._sched.get_event_position()
        path = Gtk.TreePath(pos)
        iter = self._model.get_iter(path)
        # Backup original style
        self._cell_bg_old = self._model[iter][7]
        self._cell_fg_old = self._model[iter][8]
        # Set current row color
        self._model[iter][7] = config.selected_bg_color
        self._model[iter][8] = config.selected_font_color
        self._model[iter][9] = config.selected_font
        # Scroll to current cell
        self.scroll_to_cell(path, use_align=True, row_align=0.5)

    def check_recorder(self):
        """ Return true if set """
        pos = self._sched.get_event_position()
        path = Gtk.TreePath(pos)
        iter = self._model.get_iter(path)
        if self._model[iter][10]:
            self._model[iter][10] = False
            return True
        return False

    def _init_model(self):
        """ Initialize TreeView model filled with schedule events """
        store = Gtk.TreeStore(str,              #  0 Weekday
                              bool,             #  1 IsParent
                              str,              #  2 Time
                              str,              #  3 Title
                              str,              #  4 URL
                              str,              #  5 Host
                              GdkPixbuf.Pixbuf, #  6 Icon
                              str,              #  7 BackgroundColor
                              str,              #  8 FontColor
                              str,              #  9 Font
                              bool)             # 10 Recorder set
        self._model = store.filter_new()
        self._model.set_visible_func(self._model_func)
        self._sched.fill_tree_strore(store)
        self._cell_bg_old = ''
        self._cell_fg_old = ''
        self.set_model(self._model)

    def _model_func(self, model, iter, data):
        """ Filter by weekday """
        return model[iter][0] == self._weekday_filter

    def _on_button_release_event(self, widget, event):
        """ On right click """
        if not event.button == 3:
            return
        selection = self.get_selection()
        model, iter = selection.get_selected()
        # Create popup menu
        self._popup = Gtk.Menu()
        # Program url
        url = create_menuitem(_("Program page"), "web-browser")
        url.set_size_request(100, -1)
        event_url = model.get_value(iter, 4)
        url.connect("activate", self._on_url, event_url)
        self._popup.append(url)
        # Record program
        if model.get_value(iter, 1):
            # Record main events only
            if not model.get_value(iter, 10):
                rec = create_menuitem(_("Record program"), "media-record")
                rec.connect("activate", self._on_record_set, model, iter)
            else:
                rec = create_menuitem(_("Don't record"), "gtk-cancel")
                rec.connect("activate", self._on_record_cancel, model, iter)
            self._popup.append(rec)

        self._popup.show_all()
        self._popup.popup(None, None, None, None, event.button, event.time)

    def _on_record_set(self, button, model, iter):
        """ Record program """
        model.set_value(iter, 10, True)

    def _on_record_cancel(self, button, model, iter):
        """ Cancel recording """
        model.set_value(iter, 10, False)

    def _on_url(self, button, url):
        """ Open browser """
        subprocess.Popen(['xdg-open', url], stdout=subprocess.PIPE)
