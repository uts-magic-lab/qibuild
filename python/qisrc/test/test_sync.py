## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

import os
import tempfile
import unittest
from StringIO import StringIO

import qisrc.sync
import qisrc.git
import qibuild.sh

from qisrc.test.test_git import create_git_repo, read_readme



class SyncTestCase(unittest.TestCase):
    def setUp(self):
        qibuild.command.CONFIG["quiet"] = True
        self.tmp = tempfile.mkdtemp(prefix="test-qisrc-sync")
        qibuild.sh.mkdir(self.tmp)

    def tearDown(self):
        qibuild.command.CONFIG["quiet"] = False
        qibuild.sh.rm(self.tmp)

    def test_local_manifest_sync(self):
        create_git_repo(self.tmp, "qi/libqi")
        worktree = qisrc.worktree.create(self.tmp)
        xml = """
<manifest>
    <remote name="origin"
        fetch="{tmp}"
    />

    <project name="srv/qi/libqi.git"
        path="lib/libqi"
    />
</manifest>
"""
        xml = xml.format(tmp=self.tmp)
        manifest = StringIO(xml)
        qisrc.sync.sync_projects(worktree, manifest)
        self.assertEqual(len(worktree.projects), 1)
        libqi = worktree.projects[0]
        self.assertEqual(libqi.path,
                         os.path.join(worktree.root, "lib/libqi"))

    def test_git_manifest_sync(self):
        create_git_repo(self.tmp, "qi/libqi")
        manifest_url = create_git_repo(self.tmp, "manifest")
        manifest_src = os.path.join(self.tmp, "src", "manifest")
        manifest_xml = os.path.join(manifest_src, "manifest.xml")
        xml = """
<manifest>
    <remote name="origin"
        fetch="{tmp}/srv"
    />

    <project name="qi/libqi.git"
        path="lib/libqi"
    />
</manifest>
"""
        xml = xml.format(tmp=self.tmp)
        with open(manifest_xml, "w") as fp:
            fp.write(xml)
        git = qisrc.git.Git(manifest_src)
        git.call("add", "manifest.xml")
        git.call("commit", "-m", "added manifest.xml")
        git.call("push", manifest_url, "master:master")
        worktree = qisrc.worktree.create(self.tmp)
        fetched_manifest = qisrc.sync.fetch_manifest(worktree, manifest_url)
        with open(fetched_manifest, "r") as fp:
            fetched_xml = fp.read()
        self.assertEqual(fetched_xml, xml)
        qisrc.sync.sync_projects(worktree, fetched_manifest)
        # And do it a second time, checking that we don't get an
        # 'directory not empty' git failure
        qisrc.sync.sync_projects(worktree, fetched_manifest)

    def test_git_manifest_sync_branch(self):
        # FIXME: this code is very confusing.
        # What we have here are two branches in the manifest repo:
        #  - master:  3 projects: naoqi, libnaoqi and doc
        #  - release-1.12: 2 projects: naoqi and doc, but doc stays with the
        #   'master' branch
        manifest_url = create_git_repo(self.tmp, "manifest", with_release_branch=True)
        create_git_repo(self.tmp, "naoqi", with_release_branch=True)
        create_git_repo(self.tmp, "libnaoqi")
        create_git_repo(self.tmp, "doc")
        manifest_src = os.path.join(self.tmp, "src", "manifest")
        manifest_xml = os.path.join(manifest_src, "manifest.xml")
        git = qisrc.git.Git(manifest_src)
        git.checkout("-f", "master")
        xml = """
<manifest>
    <remote name="origin" fetch="{tmp}/srv" />
    <project name="naoqi.git" path="naoqi" />
    <project name="libnaoqi.git" path="lib/libnaoqi" />
    <project name="doc" path="doc" />
</manifest>
"""
        xml = xml.format(tmp=self.tmp)
        with open(manifest_xml, "w") as fp:
            fp.write(xml)
        git.call("add", "manifest.xml")
        git.call("commit", "-m", "added manifest.xml")
        git.call("push", manifest_url, "master:master")
        git.checkout("release-1.12")
        xml = """
<manifest>
    <remote name="origin" fetch="{tmp}/srv" revision="release-1.12" />
    <project name="naoqi.git" path="naoqi" />
    <project name="doc" path="doc" revision="master" />
</manifest>
"""
        xml = xml.format(tmp=self.tmp)
        with open(manifest_xml, "w") as fp:
            fp.write(xml)
        git.call("add", "manifest.xml")
        git.call("commit", "-m", "fixed manifest.xml for 1.12")
        git.call("push", manifest_url, "release-1.12:release-1.12")
        master_root  = os.path.join(self.tmp, "work", "master")
        release_root = os.path.join(self.tmp, "work", "release-1.12")
        qibuild.sh.mkdir(master_root,  recursive=True)
        qibuild.sh.mkdir(release_root, recursive=True)
        master_wt  = qisrc.worktree.create(master_root)
        release_wt = qisrc.worktree.create(release_root)
        master_manifest  = qisrc.sync.fetch_manifest(master_wt,  manifest_url,
            branch="master")
        release_manifest = qisrc.sync.fetch_manifest(release_wt, manifest_url,
            branch="release-1.12")
        qisrc.sync.sync_projects(master_wt,  master_manifest)
        qisrc.sync.pull_projects(master_wt)
        qisrc.sync.sync_projects(release_wt, release_manifest)
        qisrc.sync.pull_projects(release_wt)
        release_srcs = [p.src for p in release_wt.projects]
        self.assertEqual(release_srcs, ["doc", "manifest/default", "naoqi"])
        naoqi_release = release_wt.get_project("naoqi")
        readme = read_readme(naoqi_release.path)
        self.assertEqual(readme, "naoqi on release-1.12\n")
        master_srcs = [p.src for p in master_wt.projects]
        self.assertEqual(master_srcs, ["doc", "lib/libnaoqi", "manifest/default", "naoqi"])
        naoqi_master = master_wt.get_project("naoqi")
        readme = read_readme(naoqi_master.path)
        self.assertEqual(readme, "naoqi\n")


    def test_manifest_wrong_revision(self):
        manifest_url = create_git_repo(self.tmp, "manifest", with_release_branch=True)
        manifest_src = os.path.join(self.tmp, "src", "manifest")
        xml = """
<manifest>
    <remote name="origin" revision="release-1.12" />
</manifest>
"""
        manifest_xml = os.path.join(manifest_src, "manifest.xml")
        with open(manifest_xml, "w") as fp:
            fp.write(xml)
        git = qisrc.git.Git(manifest_src)
        git.add("manifest.xml")
        git.commit("-m", "add manifest.xml")
        git.push(manifest_url, "release-1.12:release-1.12")
        worktree = qisrc.worktree.create(self.tmp)
        qisrc.sync.clone_project(worktree, manifest_url)
        manifest = qisrc.sync.fetch_manifest(worktree, manifest_url, branch="release-1.12")
        qisrc.sync.sync_projects(worktree, manifest)
        worktree.set_manifest_project("manifest/default")
        manifest_projects = worktree.get_manifest_projects()
        self.assertEqual(len(manifest_projects), 1)
        manifest_path = manifest_projects[0].path
        readme = read_readme(manifest_path)
        self.assertEqual(readme, "manifest on release-1.12\n")


if __name__ == "__main__":
    unittest.main()
