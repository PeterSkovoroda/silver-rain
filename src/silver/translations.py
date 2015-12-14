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

import gettext

from . import config
from gettext import gettext as _

LANGUAGES_LIST      = ["English", "Русский"]
TRANSLATIONS_LIST   = ["en", "ru"]

WEEKDAY_LIST = [_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"),
                _("Friday"), _("Saturday"), _("Sunday")]

def set_translation():
    if config.language:
        print("INSTALL")
        lang = gettext.translation("silver-rain",
                languages=[TRANSLATIONS_LIST[config.language]])
        lang.install()
    else:
        global _
        _ = lambda s: s
