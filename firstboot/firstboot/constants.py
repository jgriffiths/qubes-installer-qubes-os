#
# Chris Lumens <clumens@redhat.com>
#
# Copyright 2007 Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.  Any Red Hat
# trademarks that are incorporated in the source code or documentation are not
# subject to the GNU General Public License and may only be used or replicated
# with the express permission of Red Hat, Inc. 
#
MODE_REGULAR  = 1
MODE_RECONFIG = 2

RESULT_FAILURE = 0
RESULT_SUCCESS = 1
RESULT_JUMP = 2

BASEDIR = "/usr/share/firstboot/"


# new constants
MODULE_DIR = '/usr/share/firstboot/modules'
THEME_DIR = '/usr/share/firstboot/themes'

I18N = '/etc/sysconfig/i18n'
DISPLAY = ':9'
VT = 'vt1'

WMS = ('metacity',
       'kwin',
       'xfwm4',
       'openbox',
       'marco')

XRES = '/etc/X11/Xresources'

MODCLASS = 'moduleClass'

