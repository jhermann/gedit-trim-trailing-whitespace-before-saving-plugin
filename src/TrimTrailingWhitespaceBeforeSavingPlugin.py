# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil -*-
# Copyright © 2010–2012 Daniel Trebbien
# Copyright © 2006–2008 Osmo Salomaa
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from gi.repository import GObject, Gedit
import inspect

DEBUG_PLUGINS = Gedit.DebugSection.DEBUG_PLUGINS

# Bug 668924 - Make gedit_debug_message() introspectable <https://bugzilla.gnome.org/show_bug.cgi?id=668924>
try:
    debug_message2 = Gedit.debug_message2
    debug_message = Gedit.debug_message
except:
    def debug_message(section, filename, lineno, func_name, format_str, *args):
        Gedit.debug(section, filename, lineno, func_name)

def get_filename():
    return inspect.currentframe().f_back.f_code.co_filename

# http://code.activestate.com/recipes/145297-grabbing-the-current-line-number-easily/
def get_lineno():
    """Returns the line number of the call to get_lineno()."""

    return inspect.currentframe().f_back.f_lineno

# http://stackoverflow.com/questions/2203424/python-how-to-retrieve-class-information-from-a-frame-object
def get_func_name():
    caller_frame = inspect.currentframe().f_back
    try:
        func_name = caller_frame.f_code.co_name
        try:
            class_name = caller_frame.f_locals["self"].__class__.__name__
            return "%s.%s" % (class_name, func_name)
        except:
            return func_name
    finally:
        caller_frame = None



class TrimTrailingWhitespaceBeforeSavingPlugin(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "TrimTrailingWhitespaceBeforeSavingPlugin"

    TAB_ADDED_HANDLER_ID_KEY = "GeditTrimTrailingWhitespaceBeforeSavingPluginTabAddedHandlerId"
    SAVING_HANDLER_ID_KEY = "GeditTrimTrailingWhitespaceBeforeSavingPluginSavingHandlerId"

    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        debug_message(DEBUG_PLUGINS, get_filename(), get_lineno(), get_func_name(), "self=%r" % self)

    def __del__(self):
        debug_message(DEBUG_PLUGINS, get_filename(), get_lineno(), get_func_name(), "self=%r" % self)

    def do_activate(self):
        window = self.window

        # Connect to the 'tab-added' signal.
        handler_id = window.connect("tab-added", self.__on_window_tab_added)
        window.set_data(TrimTrailingWhitespaceBeforeSavingPlugin.TAB_ADDED_HANDLER_ID_KEY, handler_id)

        # For each document that is currently open, call __connect_document()
        # to connect all plugin-specific event handlers.
        for doc in window.get_documents():
            self.__connect_document(doc)

    def __on_window_tab_added(self, window, tab):
        doc = tab.get_document()
        self.__connect_document(doc)

    def __connect_document(self, doc):
        """Connect to the document's 'saving' signal."""

        handler_id = doc.get_data(TrimTrailingWhitespaceBeforeSavingPlugin.SAVING_HANDLER_ID_KEY)
        if handler_id is None:
            # When saving the document, call __on_document_saving().
            handler_id = doc.connect("saving", self.__on_document_saving)
            doc.set_data(TrimTrailingWhitespaceBeforeSavingPlugin.SAVING_HANDLER_ID_KEY, handler_id)

    def __disconnect_document(self, doc):
        """Disconnect from the document's 'saving' signal."""

        handler_id = doc.get_data(TrimTrailingWhitespaceBeforeSavingPlugin.SAVING_HANDLER_ID_KEY)
        doc.disconnect(handler_id)
        doc.set_data(TrimTrailingWhitespaceBeforeSavingPlugin.SAVING_HANDLER_ID_KEY, None)

    def do_deactivate(self):
        window = self.window

        # For each document that is currently open, call __disconnect_document()
        # to disconnect all plugin-specific event handlers.
        for doc in window.get_documents():
            self.__disconnect_document(doc)

        # Disconnect from the 'tab-added' signal.
        handler_id = window.get_data(TrimTrailingWhitespaceBeforeSavingPlugin.TAB_ADDED_HANDLER_ID_KEY)
        window.disconnect(handler_id)
        window.set_data(TrimTrailingWhitespaceBeforeSavingPlugin.TAB_ADDED_HANDLER_ID_KEY, None)

    def __on_document_saving(self, doc, *args):
        """Trim trailing space in the document."""

        doc.begin_user_action()
        language = doc.get_language()
        if language != None:
            language_id = language.get_id()
            if language_id != "diff":
                self.__trim_trailing_spaces_on_lines(doc)
        self.__trim_trailing_blank_lines(doc)
        doc.end_user_action()

    def __trim_trailing_blank_lines(self, doc):
        """Delete extra blank lines at the end of the document."""

        buffer_end = doc.get_end_iter()
        if buffer_end.starts_line():
            itr = buffer_end.copy()
            while itr.backward_line():
                if not itr.ends_line():
                    itr.forward_to_line_end()
                    break
            doc.delete(itr, buffer_end)

    def __trim_trailing_spaces_on_lines(self, doc):
        """Delete trailing space on each line."""

        buffer_end = doc.get_end_iter()
        for line in range(buffer_end.get_line() + 1):
            line_end = doc.get_iter_at_line(line)
            line_end.forward_to_line_end()
            itr = line_end.copy()
            while itr.backward_char():
                if not itr.get_char() in (" ", "\t"):
                    itr.forward_char()
                    break
            doc.delete(itr, line_end)
