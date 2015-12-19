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

from gi.repository import Notify

from silver.translations import _

class Notifications(Notify.Notification):
    """ Notifications """
    def __init__(self):
        Notify.Notification.__init__(self)
        self._header = _("Silver Rain")

    def show_playing(self, title, host, icon):
        """ Show notification on play """
        body = "<b>{0}</b>\n{1}".format(title, host)
        self.set_icon_from_pixbuf(icon)
        self.update(self._header, body)
        self.show()

    def show_stopped(self):
        """ Show notification on stop """
        body = "<b>{0}</b>".format(_("Stopped"))
        img = "notification-audio-stop"
        self.update(self._header, body, img)
        self.show()
