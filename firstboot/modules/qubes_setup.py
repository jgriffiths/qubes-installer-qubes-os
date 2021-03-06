#
# The Qubes OS Project, http://www.qubes-os.org
#
# Copyright (C) 2011  Tomasz Sterna <tomek@xiaoka.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#
import grp
import os
import re
import string
import subprocess
import sys
import threading
import time

import gtk
import libuser

from firstboot.config import *
from firstboot.constants import *
from firstboot.functions import *
from firstboot.module import *

import gettext
import pyudev

_ = lambda x: gettext.ldgettext("firstboot", x)
N_ = lambda x: x


def is_package_installed(pkgname):
    return not subprocess.call(['rpm', '-q', pkgname],
        stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))

def usb_keyboard_present():
    context = pyudev.Context()
    keyboards = context.list_devices(subsystem='input', ID_INPUT_KEYBOARD='1')
    return any([d.get('ID_USB_INTERFACES', False) for d in keyboards])

def started_from_usb():
    def get_all_used_devices(dev):
        stat = os.stat(dev)
        if stat.st_rdev:
            # XXX any better idea how to handle device-mapper?
            sysfs_slaves = '/sys/dev/block/{}:{}/slaves'.format(
                os.major(stat.st_rdev), os.minor(stat.st_rdev))
            if os.path.exists(sysfs_slaves):
                for slave_dev in os.listdir(sysfs_slaves):
                    for d in get_all_used_devices('/dev/{}'.format(slave_dev)):
                        yield d
            else:
                yield dev

    context = pyudev.Context()
    mounts = open('/proc/mounts').readlines()
    for mount in mounts:
        device = mount.split(' ')[0]
        if not os.path.exists(device):
            continue
        for dev in get_all_used_devices(device):
            udev_info = pyudev.Device.from_device_file(context, dev)
            if udev_info.get('ID_USB_INTERFACES', False):
                return True

    return False

class QubesChoice(object):
    instances = []
    def __init__(self, label, states, depend=None, extra_check=None,
                 replace=None, indent=False):
        self.widget = gtk.CheckButton(label)
        self.states = states
        self.depend = depend
        self.extra_check = extra_check
        self.selected = None
        self.replace = replace
        if indent:
            self.outer_widget = gtk.Alignment()
            self.outer_widget.add(self.widget)
            self.outer_widget.set_padding(0, 0, 20, 0)
        else:
            self.outer_widget = self.widget

        if self.depend is not None:
            self.depend.widget.connect('toggled', self.friend_on_toggled)
            self.friend_on_toggled(self.depend.widget)

        self.instances.append(self)


    def friend_on_toggled(self, other_widget):
        self.set_sensitive(other_widget.get_active())


    def get_selected(self):
        return self.selected if self.selected is not None \
            else self.widget.get_sensitive() and self.widget.get_active()


    def store_selected(self):
        self.selected = self.get_selected()


    def set_sensitive(self, sensitive):
        self.widget.set_sensitive(sensitive)

    @classmethod
    def on_check_advanced_toggled(cls, widget):
        selected = widget.get_active()

        # this works, because you cannot instantiate the choices in wrong order
        # (cls.instances is a list and have deterministic ordering)
        for choice in cls.instances:
            choice.set_sensitive(not selected and
                (choice.depend is None or choice.depend.get_selected()))


    @classmethod
    def get_states(cls):
        replaced = reduce(
            lambda x, y: x+y if y else x,
            (choice.replace for choice in cls.instances if
             choice.get_selected()),
            ()
        )
        for choice in cls.instances:
            if choice.get_selected():
                for state in choice.states:
                    if state not in replaced:
                        yield state


class DisabledChoice(QubesChoice):
    def __init__(self, label):
        super(DisabledChoice, self).__init__(label, ())
        self.widget.set_sensitive(False)


class moduleClass(Module):
    def __init__(self):
        Module.__init__(self)
        self.priority = 10000
        self.sidebarTitle = N_("Create VMs")
        self.title = N_("Create VMs")
        self.icon = "qubes.png"
        self.admin = libuser.admin()
        self.default_template = 'fedora-23'
        self.choices = []

    def _showErrorMessage(self, text):
        dlg = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, text)
        dlg.set_position(gtk.WIN_POS_CENTER)
        dlg.set_modal(True)
        rc = dlg.run()
        dlg.destroy()
        return None

    def apply(self, interface, testing=False):
        try:

            qubes_users = self.admin.enumerateUsersByGroup('qubes')

            if len(qubes_users) < 1:
                self._showErrorMessage(_("You must create a user account to create default VMs."))
                return RESULT_FAILURE
            else:
                self.qubes_user = qubes_users[0]

            for choice in QubesChoice.instances:
                choice.store_selected()
                choice.widget.set_sensitive(False)
            self.check_advanced.set_sensitive(False)
            interface.nextButton.set_sensitive(False)
            interface.backButton.set_sensitive(False)

            if self.progress is None:
                self.progress = gtk.ProgressBar()
                self.progress.set_pulse_step(0.06)
                self.vbox.pack_start(self.progress, True, False)
            self.progress.show()

            if testing:
                return RESULT_SUCCESS

            if self.check_advanced.get_active():
                return RESULT_SUCCESS

            errors = []

            # Finish template(s) installation, because it wasn't fully possible
            # from anaconda (it isn't possible to start a VM there).
            # This is specific to firstboot, not general configuration.
            for template in os.listdir('/var/lib/qubes/vm-templates'):
                try:
                    self.configure_template(template)
                except Exception as e:
                    errors.append((self.stage, str(e)))

            self.configure_default_template()
            self.configure_qubes()
            self.configure_network()
            if self.choice_usb.get_selected() \
                    and not self.choice_usb_with_net.get_selected():
                # Workaround for #1464 (so qvm.start from salt can't be used)
                self.run_command_in_thread(['systemctl', 'start',
                                            'qubes-vm@sys-usb.service'])

            try:
                self.configure_default_dvm()
            except Exception as e:
                errors.append((self.stage, str(e)))

            if errors:
                msg = ""
                for (stage, error) in errors:
                    msg += "{} failed:\n{}\n\n".format(stage, error)
                self.stage = "firstboot"
                raise Exception(msg)

            interface.nextButton.set_sensitive(True)
            return RESULT_SUCCESS
        except Exception as e:
            md = gtk.MessageDialog(interface.win, gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
                    self.stage + " failure!\n\n" + str(e))
            md.run()
            md.destroy()
            self.show_stage("Failure...")
            self.progress.hide()

            self.check_advanced.set_active(True)
            interface.nextButton.set_sensitive(True)

            return RESULT_FAILURE


    def show_stage(self, stage):
        self.stage = stage
        self.progress.set_text(stage)

    def run_command(self, command, stdin=None):
        try:
            os.setgid(self.qubes_gid)
            os.umask(0007)
            cmd = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=stdin)
            out = cmd.communicate()[0]
            if cmd.returncode == 0:
                self.process_error = None
            else:
                self.process_error = "{} failed:\n{}".format(command, out)
        except Exception as e:
            self.process_error = str(e)
        if self.process_error:
            # not only inform main thread, but also interrupt task thread
            raise Exception(self.process_error)

    def run_in_thread(self, method, args = None):
        thread = threading.Thread(target=method, args = (args if args else ()))
        thread.start()
        while thread.is_alive():
            self.progress.pulse()
            while gtk.events_pending():
                gtk.main_iteration(False)
            time.sleep(0.1)
        if self.process_error is not None:
            raise Exception(self.process_error)

    def run_command_in_thread(self, *args):
        self.run_in_thread(self.run_command, args)

    def configure_template(self, name):
        self.show_stage(_("Configuring TemplateVM {}".format(name)))
        self.run_in_thread(self.do_configure_template, args=(name,))

    def configure_qubes(self):
        self.show_stage('Executing qubes configuration')
        try:
            # get rid of initial entries (from package installation time)
            os.rename('/var/log/salt/minion', '/var/log/salt/minion.install')
        except OSError:
            pass
        # Refresh minion configuration to make sure all installed formulas are included
        self.run_command_in_thread(['qubesctl', 'state.sls', 'config',
            '-l', 'quiet', '--out', 'quiet'])
        for state in QubesChoice.get_states():
            self.run_command_in_thread(['qubesctl', 'top.enable', state,
                'saltenv=dom0', '-l', 'quiet', '--out', 'quiet'])
        try:
            self.run_command_in_thread(['qubesctl', 'state.highstate'])
        except Exception as e:
            raise Exception(
                "Qubes initial configuration failed. Login to the system and "
                "check /var/log/salt/minion for details. "
                "You can retry configuration by calling "
                "'sudo qubesctl state.highstate' in dom0 (you will get "
                "detailed state there).")

    def configure_default_template(self):
        self.show_stage('Setting default template')
        self.run_command_in_thread(['/usr/bin/qubes-prefs', '--set',
                'default-template', self.default_template])

    def configure_network(self):
        self.show_stage('Setting up networking')
        self.run_in_thread(
            self.do_configure_network,
            args=('sys-whonix' if self.choice_whonix_default.get_selected() else
                  'sys-firewall',))

    def configure_default_dvm(self):
        self.show_stage(_("Creating default DisposableVM"))
        self.run_in_thread(self.do_configure_default_dvm)


    def do_configure_default_dvm(self):
        try:
            self.run_command(['su', '-c', '/usr/bin/qvm-create-default-dvm --default-template --default-script', self.qubes_user])
        except:
            # Kill DispVM template if still running
            # Do not use self.run_command to not clobber process output
            subprocess.call(['qvm-kill', '{}-dvm'.format(self.default_template)])
            raise

    def do_configure_network(self, default_netvm):
        self.run_command(['/usr/bin/qvm-prefs', '--force-root', '--set', 'sys-firewall', 'netvm', 'sys-net'])
        self.run_command(['/usr/bin/qubes-prefs', '--set', 'default-netvm',
                          default_netvm])
        self.run_command(['/usr/bin/qubes-prefs', '--set', 'updatevm',
                          default_netvm])
        self.run_command(['/usr/bin/qubes-prefs', '--set', 'clockvm',
                          'sys-net'])
        self.run_command(['/usr/sbin/service', 'qubes-netvm', 'start'])

    def do_configure_template(self, template):
        self.run_command(['qvm-start', '--no-guid', template])
        self.run_command(['su', '-c',
            'qvm-sync-appmenus {}'.format(template),
            '-', self.qubes_user])
        self.run_command(['qvm-shutdown', '--wait', template])

    def createScreen(self):
        self.vbox = gtk.VBox(spacing=5)

        label = gtk.Label(_("Almost there! We just need to create a few system service VM.\n\n"
            "We can also create a few AppVMs that might be useful for most users, "
            "or you might prefer to do it yourself later.\n\n"
            "Choose an option below and click 'Finish'..."))

        label.set_line_wrap(True)
        label.set_alignment(0.0, 0.5)
        label.set_size_request(500, -1)
        self.vbox.pack_start(label, False, True, padding=20)

        self.choice_network = QubesChoice(
            _('Create default system qubes (sys-net, sys-firewall)'),
            ('qvm.sys-net', 'qvm.sys-firewall'))

        self.choice_default = QubesChoice(
            _('Create default application qubes '
                '(personal, work, untrusted, vault)'),
            ('qvm.personal', 'qvm.work', 'qvm.untrusted', 'qvm.vault'),
            depend=self.choice_network)

        if is_package_installed('qubes-template-whonix-gw') and \
                is_package_installed('qubes-template-whonix-ws'):
            self.choice_whonix = QubesChoice(
                _('Create Whonix Gateway and Workstation qubes '
                    '(sys-whonix, anon-whonix)'),
                ('qvm.sys-whonix', 'qvm.anon-whonix'),
                depend=self.choice_network)
        else:
            self.choice_whonix = DisabledChoice(_("Whonix not installed"))

        self.choice_whonix_default = QubesChoice(
            _('Route applications traffic and updates through Tor anonymity '
              'network [experimental]'),
            (),
            depend=self.choice_whonix,
            indent=True)

        if not usb_keyboard_present() and not started_from_usb():
            self.choice_usb = QubesChoice(
                _('Create USB qube holding all USB controllers (sys-usb) '
                    '[experimental]'),
                ('qvm.sys-usb',))
        else:
            self.choice_usb = DisabledChoice(
                _('USB qube configuration disabled - you are using USB '
                  'keyboard or USB disk'))

        self.choice_usb_with_net = QubesChoice(
            _("Use sys-net qube for both networking and USB devices"),
            ('qvm.sys-net-with-usb',),
            depend=self.choice_usb,
            replace=('qvm.sys-usb',),
            indent=True
        )

        self.check_advanced = gtk.CheckButton(
            _('Do not configure anything (for advanced users)'))
        self.check_advanced.connect('toggled',
            QubesChoice.on_check_advanced_toggled)

        for choice in QubesChoice.instances:
            self.vbox.pack_start(choice.outer_widget, False, True)
        #self.vbox.pack_start(gtk.HSeparator())
        self.vbox.pack_end(self.check_advanced, False, True)

        self.progress = None


    def initializeUI(self):
        self.check_advanced.set_active(False)

        self.choice_network.widget.set_active(True)
        self.choice_default.widget.set_active(True)
        if self.choice_whonix.widget.get_sensitive():
            self.choice_whonix.widget.set_active(True)

        self.qubes_gid = grp.getgrnam('qubes').gr_gid
        self.stage = "Initialization"
        self.process_error = None
