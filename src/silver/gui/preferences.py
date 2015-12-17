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
import os

import silver.config as config

from silver.globals import ICON
from silver.globals import STREAM_URL_LIST
from silver.translations import _
from silver.translations import LANGUAGES_LIST
from silver.gui.common import rgba_to_hex

class Preferences(Gtk.Dialog):
    """ Preferences window """
    def __init__(self, parent):
        Gtk.Dialog.__init__(self)
        self.set_title("Silver Rain: Preferences")
        self.set_size_request(400, 300)
        self.set_transient_for(parent)
        self.set_resizable(False)
        # Flags
        self._changed = False
        self._language_changed = False
        self._im_changed = False
        self._appearance_changed = False
        self._network_changed = False
        # Logo
        img = Gtk.Image.new_from_icon_name(ICON, 64)
        img.set_pixel_size(50)
        # Title
        title = Gtk.Label()
        title.set_markup("<span size='18000'><b>" +
                         "Silver Rain\n" +
                         "</b></span>" +
                         "<span size='11000'>" +
                         _("Preferences") +
                         "</span>")
        title.set_alignment(0, 0)
        title.set_selectable(True)
        # Pack header
        header = Gtk.HBox(spacing=5)
        header.set_border_width(10)
        header.pack_start(img, False, False, 0)
        header.pack_start(title, False, False, 0)

        def create_page():
            page = Gtk.VBox()
            page.set_border_width(15)
            return page

        def create_prefs_grid():
            grid = Gtk.Grid()
            grid.set_border_width(10)
            grid.set_column_spacing(10)
            grid.set_row_spacing(5)
            return grid

        def pack_prefs_box(page, text, grid):
            title = Gtk.Label()
            title.set_alignment(0, 0.5)
            title.set_markup("<span size='11000'><b>" + text + "</b></span>")
            page.pack_start(title, False, False, 0)
            page.pack_start(grid, False, False, 0)

        ###############
        ### General ###
        ###############
        page_general = create_page()
        ## General
        general = create_prefs_grid()
        # Autoplay
        autoplay = Gtk.CheckButton()
        autoplay.set_label(_("Autoplay on start up"))
        autoplay.set_active(config.autoplay)
        autoplay.connect("toggled", self._on_autoplay_changed)
        general.attach(autoplay, 0, 0, 2, 1)
        # Start Hidden
        start_hidden = Gtk.CheckButton()
        start_hidden.set_label(_("Start hidden"))
        start_hidden.set_active(config.start_hidden)
        start_hidden.connect("toggled", self._on_start_hidden_changed)
        general.attach_next_to(start_hidden, autoplay,
                               Gtk.PositionType.BOTTOM, 2, 1)
        # Languages
        text = Gtk.Label(_("Language:"))
        text.set_size_request(180, -1)
        text.set_alignment(0, 0.5)
        general.attach_next_to(text, start_hidden,
                               Gtk.PositionType.BOTTOM, 1, 1)
        lang_store = Gtk.ListStore(str)
        for lang in LANGUAGES_LIST:
            lang_store.append([lang])
        self._language = Gtk.ComboBox.new_with_model(lang_store)
        renderer_text = Gtk.CellRendererText()
        self._language.pack_start(renderer_text, True)
        self._language.add_attribute(renderer_text, "text", 0)
        self._language.set_active(config.language)
        self._language.connect("changed", self._on_language_changed)
        general.attach_next_to(self._language, text,
                               Gtk.PositionType.RIGHT, 1, 1)
        self._need_restart = Gtk.Label()
        self._need_restart.set_alignment(0, 0)
        self._need_restart.set_markup("<i>" + _("Requires restart") +
                                           "</i>")
        general.attach_next_to(self._need_restart, text,
                               Gtk.PositionType.BOTTOM, 2, 1)
        pack_prefs_box(page_general, _("General"), general)
        ## Recordings
        recordings = create_prefs_grid()
        text = Gtk.Label(_("Recordings directory path:"))
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        recordings.attach(text, 0, 0, 1, 1)
        self._recs_dir = Gtk.FileChooserButton()
        self._recs_dir.set_filename(config.recs_dir)
        self._recs_dir.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self._recs_dir.connect("file-set", self._on_recs_dir_changed)
        recordings.attach_next_to(self._recs_dir, text,
                                  Gtk.PositionType.RIGHT, 1, 1)
        text = Gtk.Label(_("Recordings prefix:"))
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        recordings.attach(text, 0, 1, 1, 1)
        recs_prefix = Gtk.Entry()
        recs_prefix.set_text(config.recs_prefix)
        recs_prefix.set_editable(True)
        recs_prefix.connect("changed", self._on_recs_prefix_changed)
        recordings.attach_next_to(recs_prefix, text,
                                  Gtk.PositionType.RIGHT, 1, 1)
        pack_prefs_box(page_general, _("Recordings"), recordings)
        ## Messages
        im = create_prefs_grid()
        text = Gtk.Label(_("Default message sender:"))
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        im.attach(text, 0, 0, 1, 1)
        message_header = Gtk.Entry()
        message_header.set_editable(True)
        message_header.set_text(config.message_sender)
        message_header.connect("changed", self._on_message_header_changed)
        message_header.set_placeholder_text(_("Name e-mail/phone number"))
        im.attach_next_to(message_header, text,
                          Gtk.PositionType.RIGHT, 1, 1)
        pack_prefs_box(page_general, _("Messenger"), im)
        ################
        ## Appearance ##
        ################
        page_appearance = create_page()
        # Background
        colors = create_prefs_grid()
        text = Gtk.Label(_("Background color:"))
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        colors.attach(text, 0, 0, 1, 1)
        color = Gdk.RGBA()
        color.parse(config.bg_colors[0])
        self._bg_color_light = Gtk.ColorButton.new_with_rgba(color)
        self._bg_color_light.connect("color-set",
                self._on_bg_color_light_changed)
        colors.attach_next_to(self._bg_color_light, text,
                              Gtk.PositionType.RIGHT, 1, 1)
        # Alternate background
        text = Gtk.Label(_("Alternate background color:"))
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        colors.attach(text, 0, 1, 1, 1)
        color.parse(config.bg_colors[1])
        self._bg_color_dark = Gtk.ColorButton.new_with_rgba(color)
        self._bg_color_dark.connect("color-set",
                self._on_bg_color_dark_changed)
        colors.attach_next_to(self._bg_color_dark, text,
                              Gtk.PositionType.RIGHT, 1, 1)
        # Selection
        text = Gtk.Label(_("Selection color:"))
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        colors.attach(text, 0, 2, 1, 1)
        color.parse(config.selected_bg_color)
        self._selection_color = Gtk.ColorButton.new_with_rgba(color)
        self._selection_color.connect("color-set",
                self._on_selection_color_changed)
        colors.attach_next_to(self._selection_color, text,
                              Gtk.PositionType.RIGHT, 1, 1)
        pack_prefs_box(page_appearance, _("Colors"), colors)
        # Default font
        fonts = create_prefs_grid()
        text = Gtk.Label(_("Font:"))
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        fonts.attach(text, 0, 0, 1, 1)
        self._font = Gtk.FontButton()
        self._font.set_font_name(config.font)
        self._font.connect("font-set", self._on_font_changed)
        fonts.attach_next_to(self._font, text,
                             Gtk.PositionType.RIGHT, 1, 1)
        color.parse(config.font_color)
        self._font_color = Gtk.ColorButton.new_with_rgba(color)
        self._font_color.connect("color-set", self._on_font_color_changed)
        fonts.attach_next_to(self._font_color, self._font,
                             Gtk.PositionType.RIGHT, 1, 1)
        # Selected font
        text = Gtk.Label(_("Selection font:"))
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        fonts.attach(text, 0, 1, 1, 1)
        self._selection_font = Gtk.FontButton()
        self._selection_font.set_font_name(config.selected_font)
        self._selection_font.connect("font-set",
                self._on_selection_font_changed)
        fonts.attach_next_to(self._selection_font, text,
                             Gtk.PositionType.RIGHT, 1, 1)
        color.parse(config.selected_font_color)
        self._selection_font_color = Gtk.ColorButton.new_with_rgba(color)
        self._selection_font_color.connect("color-set",
                self._on_selection_font_color_changed)
        fonts.attach_next_to(self._selection_font_color,
                             self._selection_font,
                             Gtk.PositionType.RIGHT, 1, 1)
        pack_prefs_box(page_appearance, _("Fonts"), fonts)
        ## Reset button
        reset = Gtk.Button(_("Reset default settings"))
        reset.connect("clicked", self._on_reset_appearance)
        page_appearance.pack_end(reset, False, False, 0)
        ###############
        ### Network ###
        ###############
        page_network = create_page()
        # Stream url
        network = create_prefs_grid()
        text = Gtk.Label(_("Stream url:"))
        text.set_size_request(180, -1)
        text.set_alignment(0, 0.5)
        network.attach(text, 0, 0, 1, 1)
        stream_url_store = Gtk.ListStore(str)
        stream_url_list = STREAM_URL_LIST
        # If stream address defined by user
        if config.stream_url not in stream_url_list:
            stream_url_list.append(config.stream_url)
        for url in stream_url_list:
            stream_url_store.append([url])
        stream_url = Gtk.ComboBox.new_with_model_and_entry(stream_url_store)
        stream_url.set_entry_text_column(0)
        stream_url.set_active(stream_url_list.index(config.stream_url))
        stream_url.connect("changed", self._on_stream_url_changed)
        network.attach_next_to(stream_url, text,
                               Gtk.PositionType.RIGHT, 1, 1)
        pack_prefs_box(page_network, _("Network"), network)
        # Proxy
        proxy = create_prefs_grid()
        use_proxy = Gtk.CheckButton()
        use_proxy.set_label(_("Use proxy"))
        use_proxy.set_active(config.proxy_required)
        use_proxy.connect("toggled", self._on_use_proxy)
        proxy.attach(use_proxy, 0, 0, 2, 1)

        text = Gtk.Label(_("URI:"))
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        proxy.attach(text, 0, 1, 1, 1)
        self._proxy_uri = Gtk.Entry()
        self._proxy_uri.set_text(config.proxy_uri)
        self._proxy_uri.set_editable(True)
        self._proxy_uri.set_sensitive(config.proxy_required)
        self._proxy_uri.connect("changed", self._on_proxy_uri_changed)
        proxy.attach_next_to(self._proxy_uri, text,
                             Gtk.PositionType.RIGHT, 1, 1)

        text = Gtk.Label(_("Username:"))
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        proxy.attach(text, 0, 2, 1, 1)
        self._proxy_username = Gtk.Entry()
        self._proxy_username.set_text(config.proxy_id)
        self._proxy_username.set_editable(True)
        self._proxy_username.set_sensitive(config.proxy_required)
        self._proxy_username.connect("changed",
                             self._on_proxy_username_changed)
        proxy.attach_next_to(self._proxy_username, text,
                             Gtk.PositionType.RIGHT, 1, 1)

        text = Gtk.Label(_("Password:"))
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        proxy.attach(text, 0, 3, 1, 1)
        self._proxy_password = Gtk.Entry()
        self._proxy_password.set_text(config.proxy_pw)
        self._proxy_password.set_editable(True)
        self._proxy_password.set_sensitive(config.proxy_required)
        self._proxy_password.connect("changed",
                             self._on_proxy_password_changed)
        proxy.attach_next_to(self._proxy_password, text,
                             Gtk.PositionType.RIGHT, 1, 1)

        pack_prefs_box(page_network, _("Proxy"), proxy)

        ## Notebook
        notebook = Gtk.Notebook()
        notebook.set_show_border(True)
        notebook.set_border_width(10)
        notebook.append_page(page_general, Gtk.Label(_("General")))
        notebook.append_page(page_appearance, Gtk.Label(_("Appearance")))
        notebook.append_page(page_network, Gtk.Label(_("Network")))
        ## Pack
        area = self.get_content_area()
        area.set_border_width(0)
        area.set_spacing(5)
        area.pack_start(header, False, False, 0)
        area.pack_start(notebook, True, True, 0)
        area.show_all()
        ## Buttons
        self.add_button(Gtk.STOCK_APPLY, Gtk.ResponseType.APPLY)
        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        ## Show
        self._need_restart.hide()

    def validate(self):
        """ Check recordings path for write access """
        new_path = self._recs_dir.get_filename()
        if os.access(new_path, os.W_OK):
            return True
        else:
            self._recs_dir.set_filename(config.recs_dir)
            Gtk.Widget.grab_focus(self._recs_dir)
            return False

    def apply_settings(self):
        """ Save config file """
        apply = []
        if not self._changed:
            # Nothing to apply
            return apply
        # Language
        if self._language_changed:
            LANG_OLD = config.language
            iter = self._language.get_active_iter()
            if iter:
                model = self._language.get_model()
                lang = model[iter][0]
                config.language = LANGUAGES_LIST.index(lang)
        # Get recordings dir path
        config.recs_dir = self._recs_dir.get_filename()
        # Save config file
        config.save()
        # Restore language
        if self._language_changed:
            config.language = LANG_OLD

        if self._im_changed:
            apply.append("IM")
        if self._appearance_changed:
            apply.append("APPEARANCE")
        if self._network_changed:
            apply.append("NETWORK")
        return apply

    def _on_autoplay_changed(self, button):
        config.autoplay = button.get_active()
        self._changed = True

    def _on_start_hidden_changed(self, button):
        config.start_hidden = button.get_active()
        self._changed = True

    def _on_language_changed(self, combo):
        self._need_restart.show()
        self._changed = True
        self._language_changed = True

    def _on_recs_dir_changed(self, widget):
        self._changed = True

    def _on_recs_prefix_changed(self, entry):
        self._changed = True
        config.recs_prefix = entry.get_text()

    def _on_message_header_changed(self, entry):
        config.message_sender = entry.get_text()
        self._changed = True
        self._im_changed = True

    def _on_bg_color_light_changed(self, widget):
        config.bg_colors[0] = rgba_to_hex(widget.get_rgba())
        self._changed = True
        self._appearance_changed = True

    def _on_bg_color_dark_changed(self, widget):
        config.bg_colors[1] = rgba_to_hex(widget.get_rgba())
        self._changed = True
        self._appearance_changed = True

    def _on_selection_color_changed(self, widget):
        config.selected_bg_color = rgba_to_hex(widget.get_rgba())
        self._changed = True
        self._appearance_changed = True

    def _on_font_changed(self, widget):
        config.font = self._font.get_font_name()
        self._changed = True
        self._appearance_changed = True

    def _on_font_color_changed(self, widget):
        config.font_color = rgba_to_hex(widget.get_rgba())
        self._changed = True
        self._appearance_changed = True

    def _on_selection_font_changed(self, widget):
        config.selected_font = widget.get_font_name()
        self._changed = True
        self._appearance_changed = True

    def _on_selection_font_color_changed(self, widget):
        config.selected_font_color = rgba_to_hex(widget.get_rgba())
        self._changed = True
        self._appearance_changed = True

    def _on_reset_appearance(self, widget):
        """ Reset default settings """
        color = Gdk.RGBA()
        # BG colors
        color.parse(config.Default.bg_colors[0])
        self._bg_color_light.set_rgba(color)
        color.parse(config.Default.bg_colors[1])
        self._bg_color_dark.set_rgba(color)
        config.bg_colors = config.Default.bg_colors
        # Selection color
        color.parse(config.Default.selected_bg_color)
        self._selection_color.set_rgba(color)
        config.selected_bg_color = config.Default.selected_bg_color
        # Font
        self._font.set_font_name(config.Default.font)
        config.font = config.Default.font
        color.parse(config.Default.font_color)
        self._font_color.set_rgba(color)
        config.font_color = config.Default.font_color
        # Selection font
        self._selection_font.set_font_name(config.Default.selected_font)
        config.selected_font = config.Default.selected_font
        color.parse(config.Default.selected_font_color)
        self._selection_font_color.set_rgba(color)
        config.selected_font_color = config.Default.selected_font_color
        self._appearance_changed = True
        self._changed = True

    def _on_stream_url_changed(self, widget):
        iter = widget.get_active_iter()
        if iter:
            model = widget.get_model()
            config.stream_url = model[iter][0]
        else:
            config.stream_url = widget.get_child().get_text()
        self._changed = True
        self._network_changed = True

    def _on_use_proxy(self, combo):
        state = combo.get_active()
        self._proxy_uri.set_sensitive(state)
        self._proxy_username.set_sensitive(state)
        self._proxy_password.set_sensitive(state)
        config.proxy_required = state
        self._changed = True
        self._network_changed = True

    def _on_proxy_uri_changed(self, entry):
        config.proxy_uri = entry.get_text()
        self._changed = True
        self._network_changed = True

    def _on_proxy_username_changed(self, entry):
        config.proxy_id = entry.get_text()
        self._changed = True
        self._network_changed = True

    def _on_proxy_password_changed(self, entry):
        config.proxy_pw = entry.get_text()
        self._changed = True
        self._network_changed = True
