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

from gi.repository import Gdk, Gtk
import textwrap

try:
    from gi.repository import AppIndicator3 as appindicator
    import appindicator.IndicatorCategory.SYSTEM_SERVICES as APP_CATEGORY
    APP_INDICATOR = True
except ImportError:
    APP_INDICATOR = False

from silver.globals import ICON
from silver.gui.common import create_menuitem
from silver.gui.common import get_playback_label
from silver.gui.common import get_record_label
from silver.translations import _

class StatusIcon():
    """ Status icon """
    def __init__(self, app):
        self._app = app
        self._playing = False
        self._recording = False
        self._muted = False
        self._event_title = ""
        self._event_host = ""
        self._event_time = ""
        self._event_icon = None

        if APP_INDICATOR:
            # Ubuntu workaround
            return self._appindicator_init()

        self._status_icon = Gtk.StatusIcon()
        self._status_icon.set_from_icon_name(ICON)
        # Default events
        self._status_icon.connect("activate", self._on_activate)
        self._status_icon.connect("scroll-event", self._on_scroll)
        # Popup menu
        self._status_icon.connect("popup-menu", self._on_popup)
        # Tooltip
        self._status_icon.set_property("has-tooltip", True)
        self._status_icon.connect("query-tooltip", self._tooltip)

    def update_playback_menu(self, playing):
        """ Set playback status """
        self._playing = playing
        self._update_menu()

    def update_recorder_menu(self, recording):
        """ Set recording status """
        self._recording = recording
        self._update_menu()

    def update_mute_menu(self, muted):
        """ Set muted status """
        self._muted = muted
        self._update_menu()

    def update_event(self, title, host, time, icon):
        """ Set current event """
        self._event_title = title
        self._event_host = host
        self._event_time = time
        self._event_icon = icon

    def _popup_menu_create(self):
        """ Show menu on right click """
        popup_menu = Gtk.Menu()
        if APP_INDICATOR:
            # Since appindicator doesn't support left click event
            activate = Gtk.MenuItem(_("Activate"))
            activate.connect("activate", self._on_activate)
            popup_menu.append(activate)
            separator = Gtk.SeparatorMenuItem()
            popup_menu.append(separator)
        # Playback
        text, icon = get_playback_label(not self._playing)
        play = create_menuitem(text, icon)
        play.connect("activate", self._on_playback)
        play.set_size_request(100, -1)
        # Record
        text, icon = get_record_label(not self._recording)
        record = create_menuitem(text, icon)
        record.connect("activate", self._on_recorder)
        # Mute
        mute = Gtk.CheckMenuItem(_("Mute"))
        mute.set_active(self._muted)
        mute.connect("toggled", self._on_mute)
        # IM
        im = create_menuitem(_("Send message"), "gtk-edit")
        im.connect("activate", self._on_im)
        # Preferences
        preferences = create_menuitem(_("Preferences"), "gtk-preferences")
        preferences.connect("activate", self._on_prefs)
        # Quit
        quit = create_menuitem(_("Quit"), "gtk-quit")
        quit.connect("activate", self._on_quit)
        # Separator
        sep = []
        for i in range(4):
            sep.append(Gtk.SeparatorMenuItem())
        # Pack
        for item in [play, record, sep[0], mute, sep[1],
                     im, sep[2], preferences, sep[3], quit]:
            popup_menu.append(item)
        popup_menu.show_all()
        return popup_menu

    def _tooltip(self, widget, x, y, keyboard_mode, tooltip):
        """ Show current event in tooltip """
        # Silver Rain
        silver = Gtk.Label()
        silver.set_markup("<b>{0}</b>".format(_("Silver Rain")))
        # Icon
        img = Gtk.Image.new_from_pixbuf(self._event_icon)
        # Program
        title = Gtk.Label()
        str = textwrap.fill(self._event_title, 21)
        title.set_markup("<b>" + str + "</b>")
        title.set_alignment(0, 0.5)
        host = Gtk.Label()
        str = textwrap.fill(self._event_host, 21)
        host.set_text(str)
        host.set_alignment(0, 0.5)
        time = Gtk.Label()
        time.set_text(self._event_time)
        time.set_alignment(0, 0.5)
        # Pack
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_border_width(10)
        grid = Gtk.Grid()
        grid.set_column_spacing(20)
        grid.attach(img,    0, 0, 1, 3)
        grid.attach(title,  1, 0, 1, 1)
        grid.attach(host,   1, 1, 1, 1)
        grid.attach(time,   1, 2, 1, 1)
        box.pack_start(silver, False, False, 0)
        box.pack_start(grid, False, False, 0)
        # Show
        box.show_all()
        tooltip.set_custom(box)
        return True

    def _on_activate(self, icon):
        """ Show/hide main window on left click """
        self._app.toggle()

    def _on_playback(self, button):
        """ Start/stop player """
        if not self._playing:
            self._app.play()
        else:
            self._app.stop()

    def _on_recorder(self, button):
        """ Start/stop recorder """
        if not self._recording:
            self._app.record()
        else:
            self._app.stop_record()

    def _on_mute(self, button):
        """ Mute/unmute player """
        if button.get_active():
            self._app.mute()
        else:
            self._app.unmute()

    def _on_im(self, button):
        self._app.im()

    def _on_prefs(self, button):
        self._app.prefs()

    def _on_quit(self, button):
        self._app.quit()

    def _on_popup(self, icon, button, time):
        """ Show popup menu """
        self._popup_menu = self._popup_menu_create()
        def pos_func(menu, x, y, icon):
            return (Gtk.StatusIcon.position_menu(menu, x, y, icon))
        self._popup_menu.popup(None, None, pos_func,
                               self._status_icon, button, time)

    def _on_scroll(self, icon, data):
        """ Change volume by scrolling on status icon """
        self._appindicator_on_scroll(None, 0, data.direction)

    # AppIndicator
    def _appindicator_init(self):
        """ Unity appindicator """
        self._status_icon = appindicator.Indicator.new("SilverRain", ICON,
                                                       APP_CATEGORY)
        self._status_icon.set_status(appindicator.IndicatorStatus.ACTIVE)
        self._status_icon.connect("scroll-event", self._appindicator_on_scroll)
        # Popup menu
        self._update_menu()

    def _appindicator_on_scroll(self, indicator, steps, direction):
        """ Change volume by scrolling on indicator """
        if direction == Gdk.ScrollDirection.UP:
            self._app.volume_step(5)
        elif direction == Gdk.ScrollDirection.DOWN:
            self._app.volume_step(-5)

    def _update_menu(self):
        """ Creates popup menu attached to appindicator """
        if APP_INDICATOR:
            self._status_icon.set_menu(self._popup_menu_create())
