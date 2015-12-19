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

from gi.repository import GObject
from datetime import datetime
from datetime import timedelta
import threading

from silver.msktz import MSK

class Timer():
    """ Timer """
    def __init__(self, callback):
        self._t = threading.Timer(0, None)
        self._callback = callback

    def start(self, time):
        self.cancel()
        today = datetime.now(MSK())
        now = timedelta(hours=today.hour, minutes=today.minute,
                        seconds=today.second).total_seconds()
        timeout = int(time - now)
        self._t = threading.Timer(timeout, self._on_timeout)
        self._t.start()

    def cancel(self):
        self._t.cancel()

    def _on_timeout(self):
        GObject.idle_add(self._callback)
