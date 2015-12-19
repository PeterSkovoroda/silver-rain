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

from silver.gui.common import create_toolbutton
from silver.gui.common import get_playback_label
from silver.gui.common import get_volume_label
from silver.translations import _

class ControlPanel(Gtk.Box):
    """ Playback control panel """
    def __init__(self, app):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)
        self._app = app
        self.set_spacing(6)
        self.set_border_width(6)
        # Playback Button
        text, icon = get_playback_label(True)
        self._playback = create_toolbutton(icon)
        self._playback_handler = self._playback.connect("clicked",
                                                        self._on_play)
        self._playback.set_tooltip_text(text)
        # Send message Button
        send_msg = create_toolbutton("gtk-edit")
        send_msg.connect("clicked", self._on_im)
        send_msg.set_tooltip_text(_("Send message"))
        # Separator
        sep = Gtk.SeparatorToolItem()
        # Refresh schedule Button
        self._refresh = create_toolbutton("gtk-refresh")
        self._refresh.connect("clicked", self._on_refresh)
        self._refresh.set_tooltip_text(_("Update schedule"))
        # Spinner
        self._spinner = Gtk.Spinner()
        # Status
        self._status = Gtk.Label()
        self._status.set_selectable(True)
        self._status.set_alignment(-1, 0.45)
        # Mute Button
        text, icon = get_volume_label()
        self._mute = create_toolbutton(icon)
        self._mute_handler = self._mute.connect("clicked", self._on_mute)
        self._mute.set_tooltip_text(text)
        # Volume scale
        ad = Gtk.Adjustment(value=100, lower=0, upper=100, step_increment=5,
                            page_increment=10, page_size=0)
        self._volume = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL,
                                 adjustment=ad)
        self._volume.set_property("draw-value", False)
        self._volume_handler_id = self._volume.connect("value-changed",
                                                       self._on_volume_changed)
        self._volume.set_size_request(80, 0)
        # Pack toolbar
        toolbar = Gtk.Toolbar()
        toolbar.set_orientation(Gtk.Orientation.HORIZONTAL)
        toolbar.set_style(Gtk.ToolbarStyle.ICONS)
        for x, el in enumerate ([ self._playback,
                                  send_msg,
                                  sep,
                                  self._refresh ]):
            toolbar.insert(el, x)
        # Pack panel
        self.pack_start(toolbar, False, False, 0)
        self.pack_start(self._spinner, False, False, 0)
        self.pack_start(self._status, True, False, 0)
        self.pack_end(self._volume, False, False, 0)
        self.pack_end(self._mute, False, False, 0)
        self.show_all()
        self._spinner.hide()

    def update_playback_button(self, playing):
        """ Update Play/Stop button """
        text, icon = get_playback_label(not playing)
        self._playback.set_icon_name(icon)
        self._playback.set_tooltip_text(text)
        if not playing:
            self._playback.disconnect(self._playback_handler)
            self._playback_handler = self._playback.connect("clicked",
                                                            self._on_play)
        else:
            self._playback.disconnect(self._playback_handler)
            self._playback_handler = self._playback.connect("clicked",
                                                            self._on_stop)

    def update_mute_button(self, muted):
        """ Update mute button """
        text, icon = get_volume_label(muted)
        self._mute.set_icon_name(icon)
        self._mute.set_tooltip_text(text)
        if not muted:
            self._mute.disconnect(self._mute_handler)
            self._mute_handler = self._mute.connect("clicked", self._on_mute)
        else:
            self._mute.disconnect(self._mute_handler)
            self._mute_handler = self._mute.connect("clicked", self._on_unmute)

    def update_volume_scale(self, value):
        """ Update mute menu """
        self._volume.handler_block(self._volume_handler_id)
        self._volume.set_value(value)
        self._volume.handler_unblock(self._volume_handler_id)

    def status_set_updating(self):
        """ Show spinner and "Updating" message """
        self._refresh.hide()
        self._spinner.show()
        self._spinner.start()
        msg = "<span size='12000'><b>" + \
              _("Updating schedule...") + \
              "</b></span>"
        self._status.set_text(msg)
        self._status.set_use_markup(True)

    def status_set_playing(self):
        """ Hide spinner and show currently playing """
        self._spinner.stop()
        self._spinner.hide()
        self._refresh.show()

    def status_set_text(self, msg):
        """ Show message in status """
        msg = "<span size='12000'><b>" + msg
        msg += "</b></span>"
        self._status.set_text(msg)
        self._status.set_use_markup(True)

    def _on_refresh(self, button):
        self._app.update_schedule(refresh=True)

    def _on_volume_changed(self, scale):
        value = scale.get_value()
        self._app.set_volume(int(value))

    def _on_play(self, button):
        self._app.play()

    def _on_stop(self, button):
        self._app.stop()

    def _on_im(self, button):
        self._app.im()

    def _on_mute(self, button):
        self._app.mute()

    def _on_unmute(self, button):
        self._app.unmute()
