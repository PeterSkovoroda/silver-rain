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

from datetime import timedelta
from datetime import tzinfo

########################################################################
# Timezone
# It's hard to work with utc, since schedule defined for MSK zone,
# so use timezone synchronization
class MSK(tzinfo):
    """ Moscow timezone """
    def utcoffset(self, dt):
        return timedelta(hours=3)

    def dst(self, dt):
        return timedelta(hours=0)

    def tzname(self, dt):
        return "MSK"
