# -*- coding: utf-8 -*-
#
# Copyright (C) 2013  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): Vratislav Podzimek <vpodzime@redhat.com>
#                    Martin Kolman <mkolman@redhat.com>

from pyanaconda import iutil
import unittest
import types
import os
import shutil
from test_constants import ANACONDA_TEST_DIR

class UpcaseFirstLetterTests(unittest.TestCase):

    def setUp(self):
        # create the directory used for file/folder tests
        if not os.path.exists(ANACONDA_TEST_DIR):
            os.makedirs(ANACONDA_TEST_DIR)

    def tearDown(self):
        # remove the testing directory
        shutil.rmtree(ANACONDA_TEST_DIR)

    def upcase_first_letter_test(self):
        """Upcasing first letter should work as expected."""

        # no change
        self.assertEqual(iutil.upcase_first_letter("Czech RePuBliC"),
                         "Czech RePuBliC")

        # simple case
        self.assertEqual(iutil.upcase_first_letter("czech"), "Czech")

        # first letter only
        self.assertEqual(iutil.upcase_first_letter("czech republic"),
                         "Czech republic")

        # no lowercase
        self.assertEqual(iutil.upcase_first_letter("czech Republic"),
                         "Czech Republic")

class RunProgramTests(unittest.TestCase):
    def run_program_test(self):
        """Test the _run_program method."""

        # correct calling should return rc==0
        self.assertEqual(iutil._run_program(['ls'])[0], 0)

        # incorrect calling should return rc!=0
        self.assertNotEqual(iutil._run_program(['ls', '--asdasd'])[0], 0)

        # check if an int is returned for bot success and error
        self.assertIsInstance(iutil._run_program(['ls'])[0], int)
        self.assertIsInstance(iutil._run_program(['ls', '--asdasd'])[0], int)

        # error should raise OSError
        with self.assertRaises(OSError):
            iutil._run_program(['asdasdadasd'])

    def exec_with_redirect_test(self):
        """Test execWithRedirect."""
        # correct calling should return rc==0
        self.assertEqual(iutil.execWithRedirect('ls', []), 0)

        # incorrect calling should return rc!=0
        self.assertNotEqual(iutil.execWithRedirect('ls', ['--asdasd']), 0)

    def exec_with_capture_test(self):
        """Test execWithCapture."""

        # check some output is returned
        self.assertGreater(len(iutil.execWithCapture('ls', ['--help'])), 0)

        # check no output is returned
        self.assertEqual(len(iutil.execWithCapture('true', [])), 0)

    def exec_readlines_test(self):
        """Test execReadlines."""

        # test no lines are returned
        self.assertEqual(list(iutil.execReadlines("true", [])), [])

        # test some lines are returned
        self.assertGreater(len(list(iutil.execReadlines("ls", ["--help"]))), 0)

        # check that it always returns a generator for both
        # if there is some output and if there isn't any
        self.assertIsInstance(iutil.execReadlines("ls", ["--help"]),
                              types.GeneratorType)
        self.assertIsInstance(iutil.execReadlines("true", []),
                              types.GeneratorType)

    def get_dir_size_test(self):
        """Test the getDirSize."""

        # dev null should have a size == 0
        self.assertEqual(iutil.getDirSize('/dev/null'), 0)

        # incorrect path should also return 0
        self.assertEqual(iutil.getDirSize('/dev/null/foo'), 0)

        # check if an int is always returned
        self.assertIsInstance(iutil.getDirSize('/dev/null'), int)
        self.assertIsInstance(iutil.getDirSize('/dev/null/foo'), int)

        # TODO: mock some dirs and check if their size is
        # computed correctly

    def mkdir_chain_test(self):
        """Test mkdirChain."""

        # don't fail if directory path already exists
        iutil.mkdirChain('/dev/null')
        iutil.mkdirChain('/')
        iutil.mkdirChain('/tmp')

        # create a path and test it exists
        test_folder = "test_mkdir_chain"
        test_paths = [
            "foo",
            "foo/bar/baz",
            u"foo/bar/baz",
            "",
            "čřščščřščř",
            u"čřščščřščř",
            "asdasd asdasd",
            "! spam"
        ]

        # join with the toplevel test folder and the folder for this
        # test
        test_paths = [os.path.join(ANACONDA_TEST_DIR, test_folder, p)
                      for p in test_paths]

        def create_return(path):
            iutil.mkdirChain(path)
            return path

        # create the folders and check that they exist
        for p in test_paths:
            self.assertTrue(os.path.exists(create_return(p)))

        # try to create them again - all the paths should already exist
        # and the mkdirChain function needs to handle that
        # without a traceback
        for p in test_paths:
            iutil.mkdirChain(p)

    def get_active_console_test(self):
        """Test get_active_console."""

        # at least check if a string is returned
        self.assertIsInstance(iutil.get_active_console(), str)

    def is_console_on_vt_test(self):
        """Test isConsoleOnVirtualTerminal."""

        # at least check if a bool is returned
        self.assertIsInstance(iutil.isConsoleOnVirtualTerminal(), bool)

    def strip_markup_test(self):
        """Test strip_markup."""

        # list of tuples representing a markup and its correct parsing
        markups = [
            ("", ""),
            ("a", "a"),
            ("č", "č"),
            ("<č>", ""),
            ("<a>", ""),
            ("<a><a>", ""),
            ("<a></a>", ""),
            ("<a>abc</a>", "abc"),
            ("<abc", ""),  # unclosed tag
            ("a>bc", "a>bc"),  # not a valid tag
            ("<i><b>bold</b></i>", "bold"),  # nesting
            ("<p><b>bold</b> <i>italic</i></p>", "bold italic"),
            ("  <a>text</a>", "  text"),
            (" <a> </a> ", "   "),
            ('<span color="blue">text</span>', 'text'),
            ("<<<<<<<<<<<<<<<", ""),
        ]

        # check if markup is parsed properly
        for markup, output in markups:
            self.assertEqual(iutil.strip_markup(markup), output)

    def parse_nfs_url_test(self):
        """Test parseNfsUrl."""

        # empty NFS url should return 3 blanks
        self.assertEqual(iutil.parseNfsUrl(""), ("", "", ""))

        # the string is delimited by :, there is one prefix and 3 parts,
        # the prefix is discarded and all parts after the 3th part
        # are also discarded
        self.assertEqual(iutil.parseNfsUrl("discard:options:host:path"),
                         ("options", "host", "path"))
        self.assertEqual(iutil.parseNfsUrl("discard:options:host:path:foo:bar"),
                         ("options", "host", "path"))
        self.assertEqual(iutil.parseNfsUrl(":options:host:path::"),
                         ("options", "host", "path"))
        self.assertEqual(iutil.parseNfsUrl(":::::"),
                         ("", "", ""))

        # if there is only prefix & 2 parts,
        # the two parts are host and path
        self.assertEqual(iutil.parseNfsUrl("prefix:host:path"),
                         ("", "host", "path"))
        self.assertEqual(iutil.parseNfsUrl(":host:path"),
                         ("", "host", "path"))
        self.assertEqual(iutil.parseNfsUrl("::"),
                         ("", "", ""))

        # if there is only a prefix and single part,
        # the part is the host

        self.assertEqual(iutil.parseNfsUrl("prefix:host"),
                         ("", "host", ""))
        self.assertEqual(iutil.parseNfsUrl(":host"),
                         ("", "host", ""))
        self.assertEqual(iutil.parseNfsUrl(":"),
                         ("", "", ""))

    def vt_activate_test(self):
        """Test vtActivate."""

        # pylint: disable-msg=E1101

        def raise_os_error(*args, **kwargs):
            raise OSError

        # chvt does not exist on all platforms
        # and the function needs to correctly survie that
        iutil.vtActivate.func_globals['execWithRedirect'] = raise_os_error

        self.assertEqual(iutil.vtActivate(2), False)

    def get_deep_attr_test(self):
        """Test getdeepattr."""

        # pylint: disable-msg=W0201

        class O(object):
            pass

        a = O()
        a.b = O()
        a.b1 = 1
        a.b.c = 2
        a.b.c1 = "ř"

        self.assertEqual(iutil.getdeepattr(a, "b1"), 1)
        self.assertEqual(iutil.getdeepattr(a, "b.c"), 2)
        self.assertEqual(iutil.getdeepattr(a, "b.c1"), "ř")

        # be consistent with getattr and throw
        # AttributeError if non-existent attribute is requested
        with self.assertRaises(AttributeError):
            iutil.getdeepattr(a, "")
        with self.assertRaises(AttributeError):
            iutil.getdeepattr(a, "b.c.d")

    def set_deep_attr_test(self):
        """Test setdeepattr."""

        # pylint: disable-msg=W0201
        # pylint: disable-msg=E1101

        class O(object):
            pass

        a = O()
        a.b = O()
        a.b1 = 1
        a.b.c = O()
        a.b.c1 = "ř"

        # set to a new attribute
        iutil.setdeepattr(a, "b.c.d", True)
        self.assertEqual(a.b.c.d, True)

        # override existing attribute
        iutil.setdeepattr(a, "b.c", 1234)
        self.assertEqual(a.b.c, 1234)

        # "" is actually a valid attribute name
        # that can be only accessed by getattr
        iutil.setdeepattr(a, "", 1234)
        self.assertEqual(getattr(a, ""), 1234)

        iutil.setdeepattr(a, "b.", 123)
        self.assertEqual(iutil.getdeepattr(a, "b."), 123)

        # error should raise AttributeError
        with self.assertRaises(AttributeError):
            iutil.setdeepattr(a, "b.c.d.e.f.g.h", 1234)

    def strip_accents_test(self):
        """Test strip_accents."""

        # string needs to be Unicode,
        # otherwise TypeError is raised
        with self.assertRaises(TypeError):
            iutil.strip_accents("")
        with self.assertRaises(TypeError):
            iutil.strip_accents("abc")
        with self.assertRaises(TypeError):
            iutil.strip_accents("ěščřžýáíé")

        # empty Unicode string
        self.assertEquals(iutil.strip_accents(u""), u"")

        # some Czech accents
        self.assertEquals(iutil.strip_accents(u"ěščřžýáíéúů"), u"escrzyaieuu")
        self.assertEquals(iutil.strip_accents(u"v češtině"), u"v cestine")
        self.assertEquals(iutil.strip_accents(u"měšťánek rozšíří HÁČKY"),
                                              u"mestanek rozsiri HACKY")
        self.assertEquals(iutil.strip_accents(u"nejneobhospodařovávatelnějšímu"),
                                              u"nejneobhospodarovavatelnejsimu")

        # some German umlauts
        self.assertEquals(iutil.strip_accents(u"Lärmüberhörer"), u"Larmuberhorer")
        self.assertEquals(iutil.strip_accents(u"Heizölrückstoßabdämpfung"),
                                              u"Heizolrucksto\xdfabdampfung")

        # some Japanese
        self.assertEquals(iutil.strip_accents(u"日本語"), u"\u65e5\u672c\u8a9e")
        self.assertEquals(iutil.strip_accents(u"アナコンダ"),  # Anaconda
                          u"\u30a2\u30ca\u30b3\u30f3\u30bf")

        # combined
        input_string = u"ASCI měšťánek アナコンダ Heizölrückstoßabdämpfung"
        output_string =u"ASCI mestanek \u30a2\u30ca\u30b3\u30f3\u30bf Heizolrucksto\xdfabdampfung"
        self.assertEquals(iutil.strip_accents(input_string), output_string)

    def cmp_obj_attrs_test(self):
        """Test cmp_obj_attrs."""

        # pylint: disable-msg=W0201

        class O(object):
            pass

        a = O()
        a.b = 1
        a.c = 2

        a1 = O()
        a1.b = 1
        a1.c = 2

        b = O()
        b.b = 1
        b.c = 3

        # a class should have it's own attributes
        self.assertTrue(iutil.cmp_obj_attrs(a, a, ["b", "c"]))
        self.assertTrue(iutil.cmp_obj_attrs(a1, a1, ["b", "c"]))
        self.assertTrue(iutil.cmp_obj_attrs(b, b, ["b", "c"]))

        # a and a1 should have the same attributes
        self.assertTrue(iutil.cmp_obj_attrs(a, a1, ["b", "c"]))
        self.assertTrue(iutil.cmp_obj_attrs(a1, a, ["b", "c"]))
        self.assertTrue(iutil.cmp_obj_attrs(a1, a, ["c", "b"]))

        # missing attributes are considered a mismatch
        self.assertFalse(iutil.cmp_obj_attrs(a, a1, ["b", "c", "d"]))

        # empty attribute list is not a mismatch
        self.assertTrue(iutil.cmp_obj_attrs(a, b, []))

        # attributes of a and b differ
        self.assertFalse(iutil.cmp_obj_attrs(a, b, ["b", "c"]))
        self.assertFalse(iutil.cmp_obj_attrs(b, a, ["b", "c"]))
        self.assertFalse(iutil.cmp_obj_attrs(b, a, ["c", "b"]))

    def to_ascii_test(self):
        """Test _toASCII."""

        # works with strings only, chokes on Unicode strings
        with self.assertRaises(ValueError):
            iutil._toASCII(u" ")
        with self.assertRaises(ValueError):
            iutil._toASCII(u"ABC")
        with self.assertRaises(ValueError):
            iutil._toASCII(u"Heizölrückstoßabdämpfung")

        # but empty Unicode string is fine :)
        iutil._toASCII(u"")

        # check some conversions
        self.assertEqual(iutil._toASCII(""), "")
        self.assertEqual(iutil._toASCII(" "), " ")
        self.assertEqual(iutil._toASCII("&@`'łŁ!@#$%^&*{}[]$'<>*"),
                                        "&@`'\xc5\x82\xc5\x81!@#$%^&*{}[]$'<>*")
        self.assertEqual(iutil._toASCII("ABC"), "ABC")
        self.assertEqual(iutil._toASCII("aBC"), "aBC")
        _out = "Heiz\xc3\xb6lr\xc3\xbccksto\xc3\x9fabd\xc3\xa4mpfung" 
        self.assertEqual(iutil._toASCII("Heizölrückstoßabdämpfung"), _out)

    def upper_ascii_test(self):
        """Test upperASCII."""

        self.assertEqual(iutil.upperASCII(""),"")
        self.assertEqual(iutil.upperASCII("a"),"A")
        self.assertEqual(iutil.upperASCII("A"),"A")
        self.assertEqual(iutil.upperASCII("aBc"),"ABC")
        self.assertEqual(iutil.upperASCII("_&*'@#$%^aBcžčŘ"),
                                          "_&*'@#$%^ABC\xc5\xbe\xc4\x8d\xc5\x98")
        _out = "HEIZ\xc3\xb6LR\xc3\xbcCKSTO\xc3\x9fABD\xc3\xa4MPFUNG"
        self.assertEqual(iutil.upperASCII("Heizölrückstoßabdämpfung"), _out)


    def lower_ascii_test(self):
        """Test lowerASCII."""
        self.assertEqual(iutil.lowerASCII(""),"")
        self.assertEqual(iutil.lowerASCII("A"),"a")
        self.assertEqual(iutil.lowerASCII("a"),"a")
        self.assertEqual(iutil.lowerASCII("aBc"),"abc")
        self.assertEqual(iutil.lowerASCII("_&*'@#$%^aBcžčŘ"),
                                          "_&*'@#$%^abc\xc5\xbe\xc4\x8d\xc5\x98")
        _out = "heiz\xc3\xb6lr\xc3\xbccksto\xc3\x9fabd\xc3\xa4mpfung"
        self.assertEqual(iutil.lowerASCII("Heizölrückstoßabdämpfung"), _out)

