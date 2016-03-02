## Copyright (c) 2012-2016 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

import os
import sys

import qipy.parsers

def test_simple(qipy_action, args):
    qipy_action("bootstrap", "--no-site-packages")
    python_worktree = qipy.parsers.get_python_worktree(args)
    venv_path = python_worktree.venv_path
    version = "%s.%s" % (sys.version_info.major, sys.version_info.minor)
    tabulate_path = os.path.join(venv_path, "lib", "python%s" % version, "site-packages", "tabulate.py")
    assert not os.path.exists(tabulate_path)
    qipy_action("pip", "install", "tabulate")
    assert os.path.exists(tabulate_path)
