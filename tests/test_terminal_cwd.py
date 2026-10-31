"""Terminal cwd comes from the interactive shell, not from vim/ssh or a guess."""

import importlib.machinery
import importlib.util
import os
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BIN = os.path.join(_ROOT, "bin", "omarchy-session")
_loader = importlib.machinery.SourceFileLoader("omarchy_session_cwd", _BIN)
_spec = importlib.util.spec_from_loader("omarchy_session_cwd", _loader)
m = importlib.util.module_from_spec(_spec)
_loader.exec_module(m)


class ProcTree:
    """pid -> {ppid, argv, cwd, start, error, hook}."""

    def __init__(self, nodes):
        self.nodes = nodes

    def children(self, pid):
        kids = [p for p, n in self.nodes.items() if n.get("ppid") == pid]
        return sorted(kids, key=lambda p: self.nodes[p].get("start", 0))

    def is_shell(self, pid):
        node = self.nodes.get(pid)
        if not node or node.get("missing"):
            return False
        argv = node.get("argv") or []
        name = os.path.basename(argv[0]).lstrip("-") if argv else ""
        return name in m.SHELLS

    def cwd(self, pid):
        node = self.nodes.get(pid)
        if not node or node.get("missing") or node.get("cwd_error"):
            return ""
        return node.get("cwd") or ""

    def start(self, pid):
        node = self.nodes.get(pid) or {}
        return node.get("start", 0)

    def hook(self, pid):
        node = self.nodes.get(pid) or {}
        return node.get("hook")


class AssignTerminalCwdTests(unittest.TestCase):
    def test_shell_cwd_not_the_foreground_program(self):
        proc = ProcTree({
            10: {"ppid": 1, "argv": ["ghostty"], "start": 1},
            11: {"ppid": 10, "argv": ["bash"], "cwd": "/home/eric/src", "start": 2},
            12: {"ppid": 11, "argv": ["vim"], "cwd": "/tmp/vim", "start": 3},
            13: {"ppid": 11, "argv": ["ssh"], "cwd": "/home/eric", "start": 4},
        })
        got = m.assign_terminal_directories(
            [{"stable": 1, "title": "vim"}], 10, proc, "/home/eric")
        self.assertEqual(got[0]["cwd"], "/home/eric/src")
        self.assertEqual(got[0]["source"], "proc")
        self.assertEqual(got[0]["shell_pid"], 11)

    def test_ghostty_windows_follow_shell_start_order(self):
        proc = ProcTree({
            10: {"ppid": 1, "argv": ["ghostty"], "start": 1},
            21: {"ppid": 10, "argv": ["zsh"], "cwd": "/work/first", "start": 2},
            22: {"ppid": 10, "argv": ["zsh"], "cwd": "/work/second", "start": 3},
        })
        # Input order is not creation order. stable id is.
        windows = [
            {"stable": 20, "title": "second"},
            {"stable": 10, "title": "first"},
        ]
        got = m.assign_terminal_directories(windows, 10, proc, "/home/eric")
        self.assertEqual(got[0]["cwd"], "/work/second")
        self.assertEqual(got[1]["cwd"], "/work/first")
        self.assertTrue(all(r["source"] == "proc" for r in got))

    def test_omarchy_terminal_uses_the_same_shell_child(self):
        proc = ProcTree({
            10: {"ppid": 1, "argv": ["ghostty"], "start": 1},
            11: {"ppid": 10, "argv": ["bash"], "cwd": "/home/eric", "start": 2},
        })
        got = m.assign_terminal_directories(
            [{"stable": 7, "title": "Omarchy"}], 10, proc, "/tmp")
        self.assertEqual(got[0]["cwd"], "/home/eric")
        self.assertEqual(got[0]["shell_pid"], 11)

    def test_extra_shell_on_one_window_is_a_tab(self):
        proc = ProcTree({
            10: {"ppid": 1, "argv": ["ghostty"], "start": 1},
            11: {"ppid": 10, "argv": ["bash"], "cwd": "/work", "start": 2},
            12: {"ppid": 10, "argv": ["bash"], "cwd": "/work/tab", "start": 3},
        })
        got = m.assign_terminal_directories(
            [{"stable": 1, "title": "host: /work"}], 10, proc, "/home/eric")
        self.assertEqual(got[0]["cwd"], "/work")
        self.assertEqual(got[0]["tab_pids"], [12])

    def test_ambiguous_windows_do_not_guess(self):
        proc = ProcTree({
            10: {"ppid": 1, "argv": ["ghostty"], "start": 1},
            11: {"ppid": 10, "argv": ["bash"], "cwd": "/a", "start": 2},
            12: {"ppid": 10, "argv": ["bash"], "cwd": "/b", "start": 3},
            13: {"ppid": 10, "argv": ["bash"], "cwd": "/c", "start": 4},
        })
        got = m.assign_terminal_directories(
            [{"stable": 1, "title": "one"}, {"stable": 2, "title": "two"}],
            10, proc, "/home/eric")
        self.assertEqual([r["cwd"] for r in got], ["/home/eric", "/home/eric"])
        self.assertTrue(all(r["source"] == "home" for r in got))
        self.assertTrue(all(r["shell_pid"] is None for r in got))

    def test_title_can_claim_one_shell_and_leaves_the_rest_alone(self):
        proc = ProcTree({
            10: {"ppid": 1, "argv": ["ghostty"], "start": 1},
            11: {"ppid": 10, "argv": ["bash"], "cwd": "/proj", "start": 2},
            12: {"ppid": 10, "argv": ["bash"], "cwd": "/other", "start": 3},
            13: {"ppid": 10, "argv": ["bash"], "cwd": "/third", "start": 4},
        })
        got = m.assign_terminal_directories(
            [{"stable": 1, "title": "box: /proj"}, {"stable": 2, "title": "notes"}],
            10, proc, "/home/eric")
        self.assertEqual(got[0]["cwd"], "/proj")
        self.assertEqual(got[0]["source"], "proc")
        self.assertEqual(got[1]["cwd"], "/home/eric")
        self.assertEqual(got[1]["source"], "home")

    def test_unreadable_cwd_uses_a_fresh_hook_then_home(self):
        proc = ProcTree({
            10: {"ppid": 1, "argv": ["ghostty"], "start": 1},
            11: {"ppid": 10, "argv": ["bash"], "cwd_error": True, "start": 2,
                 "hook": {"fresh": True, "atuin": "a" * 32, "cwd": "/from/hook"}},
        })
        got = m.assign_terminal_directories(
            [{"stable": 1, "title": "x"}], 10, proc, "/home/eric")
        self.assertEqual(got[0]["cwd"], "/from/hook")
        self.assertEqual(got[0]["source"], "hook")
        self.assertEqual(got[0]["atuin"], "a" * 32)
        self.assertEqual(got[0]["shell_pid"], 11)

        proc.nodes[11]["hook"] = None
        got = m.assign_terminal_directories(
            [{"stable": 1, "title": "x"}], 10, proc, "/home/eric")
        self.assertEqual(got[0]["cwd"], "/home/eric")
        self.assertEqual(got[0]["source"], "home")

    def test_vanished_terminal_pid_is_home(self):
        proc = ProcTree({})
        got = m.assign_terminal_directories(
            [{"stable": 1, "title": "gone"}], 99, proc, "/home/eric")
        self.assertEqual(got[0]["cwd"], "/home/eric")
        self.assertEqual(got[0]["source"], "home")

    def test_fresh_hook_atuin_kept_when_proc_cwd_works(self):
        proc = ProcTree({
            10: {"ppid": 1, "argv": ["ghostty"], "start": 1},
            11: {"ppid": 10, "argv": ["fish"], "cwd": "/work", "start": 2,
                 "hook": {"fresh": True, "atuin": "b" * 32, "cwd": "/stale"}},
        })
        got = m.assign_terminal_directories(
            [{"stable": 1, "title": "fish"}], 10, proc, "/home/eric")
        self.assertEqual(got[0]["cwd"], "/work")
        self.assertEqual(got[0]["source"], "proc")
        self.assertEqual(got[0]["atuin"], "b" * 32)

    def test_several_unmatched_windows_do_not_share_one_hook(self):
        proc = ProcTree({
            10: {"ppid": 1, "argv": ["ghostty"], "start": 1},
            11: {"ppid": 10, "argv": ["bash"], "cwd": "/a", "start": 2},
            12: {"ppid": 10, "argv": ["bash"], "cwd": "/b", "start": 3,
                 "hook": {"fresh": True, "atuin": "", "cwd": "/from/hook"}},
            13: {"ppid": 10, "argv": ["bash"], "cwd": "/c", "start": 4},
        })
        # Three shells, two windows, no title match: both unmatched, so neither
        # is allowed to take the hook (it might belong to the other window).
        got = m.assign_terminal_directories(
            [{"stable": 1, "title": "a"}, {"stable": 2, "title": "b"}],
            10, proc, "/home/eric")
        self.assertEqual([r["source"] for r in got], ["home", "home"])


if __name__ == "__main__":
    unittest.main()
