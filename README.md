## Introduction

This is a simple plugin for Gedit 3.x which automatically trims trailing whitespace from documents when saving. It deletes all horizontal whitespace on the ends of lines as well as extra blank lines at the end of the file.

## Installation
 0. You may need to create some directories if you haven't installed Gedit plugins locally before:

    <pre>
mkdir --parents ~/.local/share/gedit/plugins
</pre>
 1. Save the latest [`trim-trailing-whitespace-before-saving.plugin`](https://github.com/dtrebbien/gedit-trim-trailing-whitespace-before-saving-plugin/raw/master/src/trim-trailing-whitespace-before-saving.plugin) and [`TrimTrailingWhitespaceBeforeSavingPlugin.py`](https://github.com/dtrebbien/gedit-trim-trailing-whitespace-before-saving-plugin/raw/master/src/TrimTrailingWhitespaceBeforeSavingPlugin.py) to `~/.local/share/gedit/plugins`
 2. Re-start Gedit.
 3. From the Edit menu, select "Preferences".
 4. On the Plugins tab, scroll down to the entry for "Trim Trailing Whitespace Before Saving" and check the checkbox.
 5. Click Close.

## Uninstallation
 0. From the Edit menu, select "Preferences".
 1. On the Plugins tab, scroll down to the entry for "Trim Trailing Whitespace Before Saving" and uncheck the checkbox.
 2. Close Gedit.
 3. Delete `trim-trailing-whitespace-before-saving.plugin` and `TrimTrailingWhitespaceBeforeSavingPlugin.py` from `~/.local/share/gedit/plugins`.

## Notes
 *  The plugin looks at the document's syntax highlighting mode. If the highlighting mode is "Plain Text" or "Diff", then the plugin does not remove trailing whitespace.
 *  The plugin source code is based on [Osmo Salomaa](https://github.com/otsaloma)'s "Save without trailing space" plugin for Gedit 2.x that was uploaded to `http://users.tkk.fi/~otsaloma/gedit/`. The website seems to be down now, but the Internet Archive as well as this git repo hold copies of the original source files, `trailsave.gedit-plugin` and `trailsave.py`.

## License
<pre>
Copyright © 2010–2012 Daniel Trebbien
Copyright © 2006–2008 Osmo Salomaa

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 51
Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
</pre>
