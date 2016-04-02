#!/usr/bin/python3
#
# Copyright (C) 2014  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Chris Lumens <clumens@redhat.com>

__all__ = ["BZ1067707_TestCase"]

from . import TestCase, TestCaseComponent
from blivet.size import Size

class SwapWithRecommendedSizeComponent(TestCaseComponent):
    name = "SwapWithRecommendedSize"

    def __init__(self, *args, **kwargs):
        TestCaseComponent.__init__(self, *args, **kwargs)
        self.disksToCreate = [("recommended-swap-disk1", Size("1GiB"))]

    @property
    def ks(self):
        return """
bootloader --location=none
zerombr
clearpart --all --initlabel
part swap --recommended
"""

class BZ1067707_TestCase(TestCase):
    name = "1067707"
    desc = """Partition lines do not necessarily require a size to be
specified.  There are plenty of reasons why a user might not do this:  putting
a filesystem on a given pre-existing partition, giving a resize or maxsize
option, or (in this case) asking for the recommended swap size.
"""

    def __init__(self):
        TestCase.__init__(self)
        self.components = [SwapWithRecommendedSizeComponent()]
