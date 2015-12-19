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

from gi.repository import Gdk, GObject, Gtk
import logging
import requests
import urllib

import silver.config as config
from silver.globals import ICON
from silver.globals import SILVER_RAIN_URL
from silver.gui.dialog import show_dialog
from silver.translations import _

COLOR_TEXTVIEW_BORDER   = "#7C7C7C"
COLOR_INVALID           = "#FF4545"

USER_AGENT      = "Mozilla/5.0 (X11; Linux x86_64) " + \
                  "AppleWebKit/537.36 (KHTML, like Gecko) " + \
                  "Chrome/41.0.2227.0 Safari/537.36"
BITRIX_SERVER   = "http://bitrix.info/ba.js"
MESSENGER_URL   = "http://silver.ru/ajax/send_message_in_studio.php"

class Messenger():
    """ Messenger """
    def __init__(self, parent):
        # Create dialog
        self._im = Gtk.Dialog.new()
        self._im.connect("delete-event", self._on_delete_event)
        self._im.set_title("Silver Rain: Messenger")
        self._im.set_resizable(True)
        self._im.set_transient_for(parent)
        self._im.set_modal(False)
        self._im.set_default_size(250, 250)
        self._hidden = True
        self._sessid = ""
        # Logo
        img = Gtk.Image.new_from_icon_name(ICON, 64)
        img.set_pixel_size(50)
        # Title
        text = "<span size='18000'><b>Silver Rain</b></span>\n"
        text += "<span size='11000'>" + _("Send message to the studio")
        text += "</span>"
        title = Gtk.Label()
        title.set_markup(text)
        title.set_alignment(0, 0)
        title.set_selectable(True)
        # Pack header
        header = Gtk.HBox(spacing=5)
        header.set_border_width(10)
        header.pack_start(img, False, False, 0)
        header.pack_start(title, False, False, 0)
        # Sender
        self._sender = Gtk.Entry()
        self._sender.set_text(config.message_sender)
        self._sender.set_max_length(40)
        self._sender.set_placeholder_text(_("Name e-mail/phone number"))
        # Message
        self._msg = Gtk.TextView()
        self._msg.set_wrap_mode(Gtk.WrapMode.WORD)
        self._msg.set_left_margin(5)
        self._msg.set_border_window_size(Gtk.TextWindowType.TOP, 5)
        self._msg.set_border_window_size(Gtk.TextWindowType.RIGHT, 15)
        self._msg.set_border_window_size(Gtk.TextWindowType.BOTTOM, 15)
        # Scrolled window
        win = Gtk.ScrolledWindow()
        win.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        win.set_min_content_height(100)
        win.add(self._msg)
        # Scrolled window border
        eb = Gtk.EventBox()
        eb.set_border_width(1)
        eb.add(win)
        self._msg_border = Gtk.EventBox()
        self._msg_border.add(eb)
        # Set border color
        color = Gdk.RGBA()
        color.parse(COLOR_TEXTVIEW_BORDER)
        self._msg_border.override_background_color(Gtk.StateType.NORMAL, color)
        # Message status
        self._status = Gtk.Label()
        self._status.set_alignment(0.1, 0.5)
        # Pack dialog
        box = Gtk.VBox(spacing=5)
        box.set_border_width(5)
        box.pack_start(self._sender, False, False, 0)
        box.pack_start(self._msg_border, True, True, 0)
        box.pack_end(self._status, False, False, 0)
        area = self._im.get_content_area()
        area.set_border_width(0)
        area.set_spacing(0)
        area.pack_start(header, False, False, 0)
        area.pack_start(box, True, True, 0)
        # Button
        self._send_button = self._im.add_button("", Gtk.ResponseType.OK)
        self._send_button.set_label(_("Send"))
        self._send_button.connect("clicked", self._on_send)
        self._send_button.set_size_request(50, 30)
        # Ctrl+Enter to send
        agr = Gtk.AccelGroup()
        self._im.add_accel_group(agr)
        key, mod = Gtk.accelerator_parse("<Control>Return")
        self._send_button.add_accelerator("activate", agr, key, mod,
                                          Gtk.AccelFlags.VISIBLE)
        # Show
        area.show_all()
        self._status.hide()

    def show(self):
        """ Show messenger """
        if not self._hidden:
            return
        self._hidden = False
        self._im.show()
        self._msg.grab_focus()

    def update_sender(self):
        """ Update message header """
        self._sender.set_text(config.message_sender)

    def _on_delete_event(self, window, event):
        """ Hide messenger """
        self._hidden = True
        window.hide()
        return True

    def _on_send(self, button):
        """ Check if forms are empty, otherwise send the message """
        color = Gdk.RGBA()
        # Reset border color
        color.parse(COLOR_TEXTVIEW_BORDER)
        self._msg_border.override_background_color(Gtk.StateType.NORMAL, color)
        # Check sender entry
        if not self._sender.get_text_length():
            self._sender.grab_focus()
            return
        msg_buf = self._msg.get_buffer()
        # Check message length
        if not msg_buf.get_char_count():
            color.parse(COLOR_INVALID)
            self._msg_border.override_background_color(Gtk.StateType.NORMAL,
                                                       color)
            self._msg.grab_focus()
            return
        # Get message from buffer
        start = msg_buf.get_start_iter()
        end = msg_buf.get_end_iter()
        text = msg_buf.get_text(start, end, True)
        # Send message
        res = self._send_message(self._sender.get_text(), text)
        if res["type"] == "error":
            # Update status
            err = "<i>{0}</i>".format(_("Couldn't send message"))
            self._status.set_markup(err)
            self._status.show()
        elif res["type"] == "success":
            # Clear text form
            msg_buf.delete(start, end)
            # Disable button for 120 seconds
            self._send_button.set_sensitive(False)
            self._countdown(120)
            # Update status
            success = "<i>{0}</i>".format(_("Message sent"))
            self._status.set_markup(success)
            self._status.show()
        elif res["type"] == "time":
            # This should never happen, but sometimes it does
            self._send_button.set_sensitive(False)
            self._countdown(res["data"])
            # Update status
            time = "<i>{0}</i>".format(_("Couldn't send message"))
            self._status.set_markup(time)
            self._status.show()
        else:
            # This should never happen
            show_dialog(self._im, "Error", "dialog-error",
                        "Unexpected response")
            logging.error("Unexpected response type: " + res)
        # Hide status
        GObject.timeout_add(10000, self._status.hide)

    def _countdown(self, count):
        """ Set countdown timer """
        counter = count
        while counter >= 0:
            GObject.timeout_add(counter * 1000, self._countdown_func,
                                count - counter)
            counter -= 1

    def _countdown_func(self, count):
        """ Show seconds remaining """
        if count > 0:
            self._send_button.set_label(_("Send") + " (" + str(count) + "s)")
        else:
            self._send_button.set_label(_("Send"))
            self._send_button.set_sensitive(True)

    def _send_message(self, header, text):
        """ Send message in studio """
        err = {"type" : "error"}
        # FIXME
        # Emulate post request to server
        # I don't know, if it's legal, but definitely wrong.
        if not self._sessid and not self._setup_session():
            # Couldn't setup session
            return err
        # Serialize message
        message = urllib.parse.urlencode({'sessid' : self._sessid,
                                          'web_form_submit' : 'Y',
                                          'WEB_FORM_ID' : 4,
                                          'form_text_81' : header,
                                          'form_text_82' : text})
        # POST request
        try:
            resp = self._session.post(MESSENGER_URL, data=message)
        except requests.exceptions.RequestException as e:
            logging.error(str(e))
            return err
        if resp.status_code != 200:
            logging.error("Connection error {0}".format(resp.status_code))
            return err
        # Parse response
        resp_data = resp.json()
        return resp_data

    def _setup_session(self):
        """ Setup bitrix session """
        self._sessid = ""
        # Get PHPSESSID, SESSID from index page
        self._session = requests.Session()
        self._session.headers = {
                "User-Agent"        : USER_AGENT,
                "Accept"            : "text/html,application/xhtml+xml," + \
                                      "application/xml;q=0.9,image/webp," + \
                                      "*/*;q=0.8",
                "Accept-Encoding"   : "gzip, deflate, sdch",
                "Accept-Language"   : "en-US,en;q=0.8",
                "DNT"               : "1",
                "Upgrade-Insecure-Requests" : "1" }
        try:
            resp = self._session.get(SILVER_RAIN_URL)
            # Get sessid from form
            sessid = re.sub(r'^.*name="sessid" id="sessid_6" value="(.*?)".*$',
                            r'\1', resp.text)
            self._sessid = sessid
            # Get bx_user_id
            self._session.headers["Accept"] = "*/*"
            self._session.headers["Referer"] = "http://silver.ru/"
            del self._session.headers["Upgrade-Insecure-Requests"]
            resp = self._session.get(BITRIX_SERVER)

        except requests.exceptions.RequestException as e:
            logging.error(str(e))
            self._sessid = ""

        except ValueError:
            logging.error("Unexpected response")

        if not self._sessid:
            return False

        # Setup session
        self._session.headers = {
                "User-Agent"        : USER_AGENT,
                "Accept"            : "*/*",
                "Accept-Encoding"   : "gzip, deflate",
                "Accept-Language"   : "en-US,en;q=0.8,ru;q=0.6",
                "Content-Type"      : "application/x-www-form-urlencoded; " + \
                                      "charset=UTF-8",
                "X-Requested-With"  : "XMLHttpRequest" }
        return True
