"""Matching, Chrome-session snapshot, and layout-order helpers.

These do not talk to Hyprland. They lock the restore behavior that failed on
a two-profile Chrome desk: titles that move, one profile stealing the other's
windows, and a clean exit that must be allowed to put the pre-logout session
back.
"""

import importlib.machinery
import importlib.util
import json
import os
import shutil
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BIN = os.path.join(_ROOT, "bin", "omarchy-session")
_loader = importlib.machinery.SourceFileLoader("omarchy_session", _BIN)
_spec = importlib.util.spec_from_loader("omarchy_session", _loader)
m = importlib.util.module_from_spec(_spec)
_loader.exec_module(m)

GMAIL = "Inbox (345) - bonanzaeric@gmail.com - Gmail - Google Chrome"
GMAIL_SHORT = "Gmail - Google Chrome"
DORMOUSE = "Inbox (1,811) - eric@dormouse.com - dormouse limited Mail - Google Chrome"
JLCPCB = "PCB Prototype & PCB Fabrication Manufacturer - JLCPCB - Google Chrome"
JLCPCB_SHORT = "JLCPCB - Google Chrome"
YOUTUBE = "SpaceX conducts Static Fire of Booster 22 - YouTube - Google Chrome"
MONITOR = "monitor - Google Chrome"
AGENDA = "agenda - Google Chrome"


class TitleMatchTests(unittest.TestCase):
    def test_unread_count_does_not_change_the_window(self):
        other = "Inbox (2) - bonanzaeric@gmail.com - Gmail - Google Chrome"
        self.assertEqual(m.title_similarity(GMAIL, other), 1.0)

    def test_short_site_title_matches_the_full_one(self):
        self.assertGreaterEqual(m.title_similarity(JLCPCB, JLCPCB_SHORT), m._TITLE_ACCEPT)
        self.assertGreaterEqual(m.title_similarity(MONITOR, "monitor - Google Chrome"), 1.0)

    def test_two_inboxes_do_not_cross(self):
        self.assertLess(m.title_similarity(GMAIL, DORMOUSE), m._TITLE_ACCEPT)
        self.assertFalse(m.only_candidate_match(DORMOUSE, GMAIL_SHORT))

    def test_loading_gmail_title_matches_only_when_it_is_the_last_window(self):
        self.assertLess(m.title_similarity(GMAIL, GMAIL_SHORT), m._TITLE_ACCEPT)
        self.assertTrue(m.only_candidate_match(GMAIL, GMAIL_SHORT))
        saved = [{"title": GMAIL, "workspace": 5}, {"title": YOUTUBE, "workspace": 5},
                 {"title": JLCPCB, "workspace": 4}]
        clients = [{"title": GMAIL_SHORT, "profile": "Default", "address": "a"}]
        pairs, notes = m.match_saved_windows(saved, clients, "Default")
        self.assertEqual(pairs, [])
        self.assertEqual(len(notes), 3)
        pairs, notes = m.match_saved_windows(
            [{"title": GMAIL, "workspace": 5}], clients, "Default")
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0][0], 0)
        self.assertEqual(notes, [])

    def test_profiles_do_not_take_each_others_windows(self):
        saved = [{"title": GMAIL, "workspace": 5}, {"title": JLCPCB, "workspace": 4}]
        clients = [
            {"title": DORMOUSE, "profile": "Profile 1", "address": "p1"},
            {"title": JLCPCB, "profile": "Default", "address": "jlc"},
            {"title": GMAIL, "profile": "Default", "address": "gm"},
        ]
        pairs, notes = m.match_saved_windows(saved, clients, "Default")
        got = {clients[ci]["address"] for _wi, ci, _s in pairs}
        self.assertEqual(got, {"jlc", "gm"})
        self.assertEqual(notes, [])
        dormouse_saved = [{"title": DORMOUSE, "workspace": 2}, {"title": MONITOR, "workspace": 2},
                          {"title": AGENDA, "workspace": 1}]
        pairs, notes = m.match_saved_windows(dormouse_saved, clients, "Profile 1")
        self.assertEqual(len(pairs), 1)
        self.assertEqual(clients[pairs[0][1]]["address"], "p1")
        self.assertEqual(len(notes), 2)

    def test_same_desk_as_the_reboot_log(self):
        """Second login: five Chrome titles came back; Gmail was still 'Gmail'."""
        default = [
            {"title": "TIDAL - Google Chrome", "workspace": 5},
            {"title": GMAIL, "workspace": 5},
            {"title": JLCPCB, "workspace": 4},
        ]
        clients = [
            {"title": "TIDAL - Google Chrome", "profile": "Default", "address": "t"},
            {"title": GMAIL_SHORT, "profile": "Default", "address": "g"},
            {"title": JLCPCB_SHORT, "profile": "Default", "address": "j"},
            {"title": DORMOUSE, "profile": "Profile 1", "address": "d"},
            {"title": MONITOR, "profile": "Profile 1", "address": "m"},
            {"title": AGENDA, "profile": "Profile 1", "address": "a"},
        ]
        pairs, notes = m.match_saved_windows(default, clients, "Default")
        self.assertEqual(notes, [])
        self.assertEqual({clients[ci]["address"] for _w, ci, _s in pairs}, {"t", "g", "j"})


class LeftoverClaimTests(unittest.TestCase):
    def test_finished_profile_does_not_claim_the_other_profiles_windows(self):
        clients = [
            {"address": "mine", "class": "google-chrome", "profile": "Profile 1"},
            {"address": "other", "class": "google-chrome", "profile": "Default"},
            {"address": "unknown", "class": "google-chrome", "profile": ""},
            {"address": "term", "class": "ghostty", "profile": ""},
        ]
        claimed = m.leftover_claim_ids("Profile 1", "google-chrome", True, clients)
        self.assertEqual(claimed, ["mine"])

    def test_last_group_can_claim_an_unknown_window(self):
        clients = [{"address": "unknown", "class": "google-chrome", "profile": ""}]
        claimed = m.leftover_claim_ids("Default", "google-chrome", False, clients)
        self.assertEqual(claimed, ["unknown"])


class LayoutOrderTests(unittest.TestCase):
    def test_column_groups_and_inversions(self):
        groups = m.column_groups([("a", 12), ("b", 20), ("c", 1727)])
        self.assertEqual([[i for i, _x in g] for g in groups], [["a", "b"], ["c"]])
        desired = ["a", "b", "c"]
        self.assertEqual(m.inversion_index(["c", "a", "b"], desired), 0)
        self.assertIsNone(m.inversion_index(desired, desired))

    def test_session_stamp_is_newer_than_any_existing_file(self):
        self.assertEqual(m.next_session_stamp(["Session_10", "Tabs_12", "notes"]), 13)
        self.assertEqual(m.next_session_stamp([]), 1)


class ChromeSessionSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.ud = os.path.join(self.tmp, "google-chrome")
        self.prof = "Default"
        self.sessions = os.path.join(self.ud, self.prof, "Sessions")
        os.makedirs(self.sessions)
        self.side = m.chrome_sidecar_dir(self.ud, self.prof)
        self.addCleanup(shutil.rmtree, self.side, True)

    def _prefs(self, exit_type, clean):
        with open(os.path.join(self.ud, self.prof, "Preferences"), "w") as f:
            json.dump({"profile": {"exit_type": exit_type, "exited_cleanly": clean}}, f)

    def _sidecar(self, payload=b"SNSS-full-session"):
        os.makedirs(self.side, mode=0o700, exist_ok=True)
        with open(os.path.join(self.side, "Session"), "wb") as f:
            f.write(payload)
        with open(os.path.join(self.side, "Tabs"), "wb") as f:
            f.write(b"SNSS-tabs")

    def test_clean_exit_installs_a_newer_snapshot_and_keeps_the_old_file(self):
        with open(os.path.join(self.sessions, "Session_10"), "wb") as f:
            f.write(b"SNSS-collapsed")
        with open(os.path.join(self.sessions, "Tabs_10"), "wb") as f:
            f.write(b"SNSS-collapsed-tabs")
        self._prefs("Crashed", False)
        self._sidecar()
        ok, why = m.install_chromium_session(self.ud, self.prof, running=False, enabled=True)
        self.assertFalse(ok)
        self.assertEqual(why, "clean-exit")
        self.assertFalse(os.path.exists(os.path.join(self.sessions, "Session_11")))

        self._prefs("Normal", True)
        ok, why = m.install_chromium_session(self.ud, self.prof, running=True, enabled=True)
        self.assertEqual((ok, why), (False, "already-running"))

        ok, why = m.install_chromium_session(self.ud, self.prof, running=False, enabled=False)
        self.assertEqual((ok, why), (False, "disabled"))

        ok, why = m.install_chromium_session(self.ud, self.prof, running=False, enabled=True)
        self.assertEqual((ok, why), (True, "installed"))
        installed = os.path.join(self.sessions, "Session_11")
        with open(installed, "rb") as f:
            data = f.read()
        self.assertEqual(data, b"SNSS-full-session")
        with open(os.path.join(self.sessions, "Tabs_11"), "rb") as f:
            self.assertEqual(f.read(), b"SNSS-tabs")
        with open(os.path.join(self.sessions, "Session_10"), "rb") as f:
            self.assertEqual(f.read(), b"SNSS-collapsed")
        self.assertEqual(os.stat(installed).st_mode & 0o777, 0o600)

    def test_save_copies_the_newest_snss_pair(self):
        with open(os.path.join(self.sessions, "Session_1"), "wb") as f:
            f.write(b"SNSS-old")
        with open(os.path.join(self.sessions, "Session_9"), "wb") as f:
            f.write(b"SNSS-current")
        with open(os.path.join(self.sessions, "Tabs_9"), "wb") as f:
            f.write(b"SNSS-current-tabs")
        with open(os.path.join(self.sessions, "Session_broken"), "wb") as f:
            f.write(b"nope")
        argv = ["google-chrome", "--user-data-dir=" + self.ud, "--profile-directory=Default"]
        m.copy_chromium_sessions({
            "items": [{"kind": "browser", "profile": "Default", "argv": argv}],
        })
        with open(os.path.join(self.side, "Session"), "rb") as f:
            self.assertEqual(f.read(), b"SNSS-current")
        with open(os.path.join(self.side, "Tabs"), "rb") as f:
            self.assertEqual(f.read(), b"SNSS-current-tabs")

    def test_restore_flag_is_added_for_chromium_only(self):
        argv = m.with_restore_last_session(["/usr/bin/google-chrome-stable", "--profile-directory=Default"])
        self.assertIn("--restore-last-session", argv)
        again = m.with_restore_last_session(argv)
        self.assertEqual(again.count("--restore-last-session"), 1)
        ff = m.with_restore_last_session(["firefox"])
        self.assertNotIn("--restore-last-session", ff)


class NotifyTests(unittest.TestCase):
    def test_unmatched_titles_do_not_fit_in_a_notification(self):
        # The notification builder rejects anything that is not a count.
        with self.assertRaises(TypeError):
            m.restore_notify_message("incomplete", placed=GMAIL, total=1)
        summary, body = m.restore_notify_message("incomplete", placed=5, total=9)
        self.assertNotIn("Inbox", summary + body)
        self.assertNotIn("@", summary + body)




class MidUpgradeChromeTests(unittest.TestCase):
    """artoo 2026-10-28: Chrome upgraded while running collapsed profiles on save."""

    def test_strip_deleted_exe(self):
        self.assertEqual(m.strip_deleted("/opt/google/chrome/chrome (deleted)"),
                         "/opt/google/chrome/chrome")
        self.assertEqual(m.strip_deleted("/opt/google/chrome/chrome"),
                         "/opt/google/chrome/chrome")

    def test_proc_basename_from_concatenated_argv_and_deleted_exe(self):
        self.assertEqual(
            m.proc_basename(
                ["/opt/google/chrome/chrome --type=zygote --no-zygote-sandbox"],
                "/opt/google/chrome/chrome (deleted)"),
            "chrome")
        self.assertEqual(
            m.proc_basename([], "/opt/google/chrome/chrome (deleted)"),
            "chrome")

    def test_chromium_user_data_recovers_from_deleted_exe(self):
        ud = os.path.join(os.path.expanduser("~"), ".config", "google-chrome")
        if not os.path.isdir(ud):
            self.skipTest("no ~/.config/google-chrome on this host")
        got = m.chromium_user_data(
            "chrome --type=zygote",
            "/opt/google/chrome/chrome (deleted)",
            ["/opt/google/chrome/chrome --type=gpu"],
            class_hint="google-chrome")
        self.assertEqual(got, ud)

    def test_save_guard_refuses_collapsed_profiles(self):
        old = {"items": [
            {"kind": "browser", "class": "google-chrome", "profile": "Default",
             "windows": [{"title": "a"}, {"title": "b"}, {"title": "c"}]},
            {"kind": "browser", "class": "google-chrome", "profile": "Profile 1",
             "windows": [{"title": "d"}, {"title": "e"}, {"title": "f"}]},
        ]}
        collapsed = {"items": [
            {"kind": "browser", "class": "google-chrome", "profile": "",
             "windows": [{"title": x} for x in "abcdef"]},
        ]}
        self.assertTrue(m.would_collapse_chrome_profiles(old, collapsed))
        self.assertFalse(m.would_collapse_chrome_profiles(old, old))
        self.assertFalse(m.would_collapse_chrome_profiles(collapsed, old))

if __name__ == "__main__":
    unittest.main()
