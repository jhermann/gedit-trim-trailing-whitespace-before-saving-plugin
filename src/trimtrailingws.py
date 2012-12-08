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

from gi.repository import GObject, Gtk, Gedit
import inspect
import re

def get_trace_info(num_back_frames=0):
    frame = inspect.currentframe().f_back
    try:
        for i in range(num_back_frames):
            frame = frame.f_back

        filename = frame.f_code.co_filename

        # http://code.activestate.com/recipes/145297-grabbing-the-current-line-number-easily/
        lineno = frame.f_lineno

        func_name = frame.f_code.co_name
        try:
            # http://stackoverflow.com/questions/2203424/python-how-to-retrieve-class-information-from-a-frame-object
            cls_name = frame.f_locals["self"].__class__.__name__
        except:
            pass
        else:
            func_name = "%s.%s" % (cls_name, func_name)

        return (filename, lineno, func_name)
    finally:
        frame = None

# Bug 668924 - Make gedit_debug_message() introspectable <https://bugzilla.gnome.org/show_bug.cgi?id=668924>
try:
    debug_plugin_message = Gedit.debug_plugin_message
except:
    def debug_plugin_message(format_str, *format_args):
        filename, lineno, func_name = get_trace_info(1)
        Gedit.debug(Gedit.DebugSection.DEBUG_PLUGINS, filename, lineno, func_name)


class TrimTrailingWhitespaceBeforeSavingPlugin(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "TrimTrailingWhitespaceBeforeSavingPlugin"

    TAB_ADDED_HANDLER_ID_KEY = "GeditTrimTrailingWhitespaceBeforeSavingPluginTabAddedHandlerId"
    SAVING_HANDLER_ID_KEY = "GeditTrimTrailingWhitespaceBeforeSavingPluginSavingHandlerId"

    WHITESPACE_CHARS = "\t\v\f "

    # GtkTextBuffer considers line ends to consist of either a newline, a carriage return,
    # a carriage return followed by a newline, or a Unicode paragraph separator character.
    # <http://developer.gnome.org/gtk3/stable/GtkTextIter.html#gtk-text-iter-ends-line>
    EOL_WHITESPACE_RE = re.compile(u"[^\n\r\u2029]*?([" + WHITESPACE_CHARS + u"]*)(?:\n|\r|\r\n|\u2029)")

    window = GObject.property(type = Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)

        debug_plugin_message("self=%r", self)

    def __del__(self):
        debug_plugin_message("self=%r", self)

    def do_activate(self):
        window = self.window

        # Connect to the 'tab-added' signal.
        handler_id = window.connect("tab-added", self.__on_window_tab_added)
        setattr(window, TrimTrailingWhitespaceBeforeSavingPlugin.TAB_ADDED_HANDLER_ID_KEY, handler_id)

        # For each document that is currently open, call __connect_document()
        # to connect all plugin-specific event handlers.
        for doc in window.get_documents():
            self.__connect_document(doc)

    def __on_window_tab_added(self, window, tab):
        doc = tab.get_document()
        self.__connect_document(doc)

    def __connect_document(self, doc):
        """Connect to the document's 'saving' signal."""

        try:
            getattr(doc, TrimTrailingWhitespaceBeforeSavingPlugin.SAVING_HANDLER_ID_KEY)
        except AttributeError:
            # When saving the document, call __on_document_saving().
            handler_id = doc.connect("saving", self.__on_document_saving)
            setattr(doc, TrimTrailingWhitespaceBeforeSavingPlugin.SAVING_HANDLER_ID_KEY, handler_id)

        if not hasattr(doc, "saved_handler_id"):
            doc.saved_handler_id = doc.connect("saved", self.__on_document_saved)

    def __disconnect_document(self, doc):
        """Disconnect from the document's 'saving' signal."""

        try:
            saved_handler_id = getattr(doc, "saved_handler_id")
        except AttributeError:
            pass
        else:
            doc.disconnect(saved_handler_id)
            del doc.saved_handler_id

        try:
            handler_id = getattr(doc, TrimTrailingWhitespaceBeforeSavingPlugin.SAVING_HANDLER_ID_KEY)
        except AttributeError:
            pass
        else:
            doc.disconnect(handler_id)
            delattr(doc, TrimTrailingWhitespaceBeforeSavingPlugin.SAVING_HANDLER_ID_KEY)

    def do_deactivate(self):
        window = self.window

        # For each document that is currently open, call __disconnect_document()
        # to disconnect all plugin-specific event handlers.
        for doc in window.get_documents():
            self.__disconnect_document(doc)

        # Disconnect from the 'tab-added' signal.
        try:
            handler_id = getattr(window, TrimTrailingWhitespaceBeforeSavingPlugin.TAB_ADDED_HANDLER_ID_KEY)
        except AttributeError:
            pass
        else:
            window.disconnect(handler_id)
            delattr(window, TrimTrailingWhitespaceBeforeSavingPlugin.TAB_ADDED_HANDLER_ID_KEY)

    def __on_document_saving(self, doc, *args):
        """Trim trailing space in the document."""

        if hasattr(doc, "current_lineno"):
            return

        cursor_position = doc.get_property("cursor-position")
        it = doc.get_iter_at_offset(cursor_position)
        doc.current_lineno = it.get_line()
        bol = it.copy()
        if not bol.starts_line():
            bol.set_line_offset(0)
            assert bol.starts_line()
        eol = it.copy()
        if not eol.ends_line():
            eol.forward_to_line_end()
        tb_slice = doc.get_slice(bol, eol, False)
        tb_slice = unicode(tb_slice, 'utf-8')
        rstripped_tb_slice = tb_slice.rstrip(TrimTrailingWhitespaceBeforeSavingPlugin.WHITESPACE_CHARS)
        doc.current_line_trailing_whitespace = tb_slice[len(rstripped_tb_slice):it.get_line_offset()]

        doc.begin_user_action()
        language = doc.get_language()
        if language != None:
            language_id = language.get_id()
            if language_id != "diff":
                self.__trim_trailing_spaces_on_lines(doc)
        self.__trim_trailing_blank_lines(doc)
        doc.end_user_action()

    def __on_document_saved(self, doc, err):
        try:
            current_lineno = getattr(doc, "current_lineno")
            current_line_trailing_whitespace = getattr(doc, "current_line_trailing_whitespace")
        except AttributeError:
            pass
        else:
            del doc.current_line_trailing_whitespace
            del doc.current_lineno
            if len(current_line_trailing_whitespace) > 0:
                it = doc.get_iter_at_line(current_lineno)
                if it.get_line() == current_lineno:
                    if not it.ends_line():
                        it.forward_to_line_end()
                    Gtk.TextBuffer.insert(doc, it, current_line_trailing_whitespace, -1)
                    doc.set_modified(False)

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

        start = doc.get_start_iter()
        end = doc.get_end_iter()
        tb_slice = doc.get_slice(start, end, False)
        tb_slice = unicode(tb_slice, 'utf-8')
        eol_whitespace_re = TrimTrailingWhitespaceBeforeSavingPlugin.EOL_WHITESPACE_RE
        lineno = 0
        for match in eol_whitespace_re.finditer(tb_slice):
            start_line_offset = match.start(1) - match.start()
            end_line_offset = match.end(1) - match.start()
            if start_line_offset != end_line_offset:
                start.set_line(lineno)
                start.set_line_offset(start_line_offset)
                end.set_line(lineno)
                end.set_line_offset(end_line_offset)
                if not end.ends_line():
                    end.forward_to_line_end()
                # This looks bad---deleting parts of the buffer while traversing
                # forward through it---but it's actually fine because the `start'
                # and `end' iterators are re-positioned relative to offsets within
                # lines, and we aren't changing the number of lines here.
                doc.delete(start, end)
            lineno = lineno + 1
