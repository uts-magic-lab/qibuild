## Copyright (c) 2012, 2013 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

"""Collection of parser fonctions for various actions."""

import abc
import os

import qisys.sh

def log_parser(parser):
    """Given a parser, add the options controlling log."""
    group = parser.add_argument_group("logging options")
    group.add_argument("-v", "--verbose", dest="verbose", action="store_true",
         help="Output debug messages")
    group.add_argument("--quiet", "-q", dest="quiet", action="store_true",
        help="Only output error messages")
    group.add_argument("--no-color", dest="color", action="store_false",
        help="Do not use color")
    group.add_argument("--time-stamp", dest="timestamp", action="store_true",
        help="Add timestamps before each log message")
    group.add_argument("--color", dest = "color", action = "store_false",
                       help = "Colorize output. This is the default")

    parser.set_defaults(verbose=False, quiet=False, color=True)

def default_parser(parser):
    """Parser settings for every action."""
    # Every action should have access to a proper log
    log_parser(parser)
    # Every action can use  --pdb and --backtrace
    group = parser.add_argument_group("debug options")
    group.add_argument("--backtrace", action="store_true", help="Display backtrace on error")
    group.add_argument("--pdb", action="store_true", help="Use pdb on error")
    group.add_argument("--quiet-commands", action="store_true", dest="quiet_commands",
        help="Do not print command outputs")

def worktree_parser(parser):
    """Parser settings for every action using a work tree."""
    default_parser(parser)
    parser.add_argument("-w", "--worktree", "--work-tree", dest="worktree",
        help="Use a specific work tree path.")

def project_parser(parser, positional=True, short=True):
    """Parser settings for every action using projects."""
    group = parser.add_argument_group("projects specifications options")
    group.add_argument("-a", "--all", action="store_true",
        help="Work on all projects")
    group.add_argument("-s", "--single", action="store_true",
        help="Work on specified projects without taking dependencies into account.")
    if positional:
        parser.add_argument("projects", nargs="*", metavar="PROJECT", help="Project name(s)")
    else:
        if short:
            group.add_argument("-p", "--project", dest="projects", action="append",
                    help="Project name(s)")
        else:
            group.add_argument("--project", dest="projects", action="append",
                    help="Project name(s)")
    parser.set_defaults(single=False, projects = list())
    return group


class AbstractProjectParser:
    """ Helper for get_projects() methods """
    __metaclass__ = abc.ABCMeta
    def __init__(self):
        pass

    @abc.abstractmethod
    def parse_no_args(self):
        pass

    @abc.abstractmethod
    def parse_one_arg(self):
        pass

    @abc.abstractmethod
    def all_projects(self):
        pass

    def parse_args(self, args):
        if args.all:
            return self.all_projects()
        project_args = args.projects
        if not args.projects:
            return self.parse_no_args()
        res = list()
        for arg in project_args:
            # parsing one arg can result in several projets
            # (for instance if there are deps)
            res.extend(self.parse_one_arg(arg))
        return res

class WorkTreeProjectParser(AbstractProjectParser):
    """ Implements AbstractProjectParser for a basic WorkTree """

    def __init__(self, worktree):
        self.worktree = worktree

    def all_projects(self):
        return self.worktree.projects

    def parse_no_args(self):
        """ Try to find the closest worktree project that
        mathes the current directory

        """
        parent_project = self._find_parent_project(os.getcwd())
        if parent_project:
            return [parent_project]

    def parse_one_arg(self, arg):
        """ Accept both an absolute path matching a worktree project,
        or a project src

        """
        # assume absolute path
        as_path = qisys.sh.to_native_path(arg)
        if os.path.exists(as_path):
            parent_project = self._find_parent_project(as_path)
            if parent_project:
                return [parent_project]

        # Now assume it is a project src
        project = self.worktree.get_project(arg, raises=True)
        return [project]


    def _find_parent_project(self, path):
        """ Find the parent project of a given path """
        projects = self.worktree.projects[:]
        projects.reverse()
        for project in projects:
            if qisys.sh.is_path_inside(path, project.path):
                return project
