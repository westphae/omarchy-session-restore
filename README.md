# Session Restore for Omarchy (`eric.session-restore`)

**macOS-like session restore for Omarchy / Hyprland.**

Reboot, log out, or crash — and come back to the same apps on the same
workspaces: terminals in the folders you left them, Chrome profiles with their
tabs, coding agents back in the same conversation. Dock your laptop and get
the docked layout; undock and get the laptop layout. No manual rearrange.

Omarchy already has a great desktop. What it does not ship is “put my windows
back.” This plugin fills that gap with a keep-loaded service that autosaves
quietly and restores once on the next login.

| | |
|---|---|
| **Plugin id** | `eric.session-restore` |
| **Version** | 1.4.6 |
| **License** | MIT |
| **Author** | Eric Westphal ([@westphae](https://github.com/westphae)) |
| **Based on** | [wbarakat/omarchy-session-restore](https://github.com/wbarakat/omarchy-session-restore) (MIT, © 2026 Waleed) |

---

## How this differs from desk save-slot plugins

Plugins such as **Tableau by Novuon** save a desktop under a name
(**Capture Current Desktop**) and switch to that desk when you ask.
`Super` + `Alt` + `T` opens the switcher. Switching closes the desktop you
are on. Tableau waits until you pick a desk; it does not restore one at login.

Session Restore is the automatic one. It keeps a quiet copy of whatever you
are already doing and puts those same windows back after a reboot or logout.

---

## Install

You need **Omarchy 4.5 or newer**, with the plugin system (`omarchy plugin …`).

Open a terminal (`Super` + `Return`) and paste:

```bash
omarchy plugin add https://github.com/westphae/omarchy-session-restore.git --enable
```

Omarchy warns you that a plugin runs as your user, then asks you to confirm.
Say yes. Omarchy clones this repo into
`~/.config/omarchy/plugins/eric.session-restore` and turns it on. Autosave
and restore start on their own.

That Git URL is the supported install. Use the same URL in the menu below.

### From the Omarchy menu

`Super` + `Space` → **Setup** → **Plugins** → **Add Plugin**.

A terminal opens and asks for a Git URL. Paste:

```text
https://github.com/westphae/omarchy-session-restore.git
```

Confirm the prompts. When it asks whether to enable the plugin, say yes.
The command above passes `--enable` for you; the menu waits for that answer.
If you leave it off, turn it on later from
**Setup → Plugins → Enable Plugin**, or:

```bash
omarchy plugin enable eric.session-restore
```

### Optional follow-ups

Skip all of these and the plugin still saves and restores. Each one adds
something specific.

**1. A short command.** So you can type `omarchy-session` in a terminal.
Omarchy’s default shell already includes `~/.local/bin`. The menu rows in
step 2 call this path.

```bash
ln -sf ~/.config/omarchy/plugins/eric.session-restore/bin/omarchy-session ~/.local/bin/omarchy-session
```

**2. Menu rows, for a snapshot as you leave.** **System → Logout**,
**Reboot**, and **Shutdown** save your windows once more before Omarchy
closes them, and **System → Save Session** shows up. Do step 1 first.

Without these rows, a reboot still restores the latest autosave, which can
be about a minute old. The rows matter because Omarchy closes windows on the
way out, and a save in the middle of that can record a half-empty desk. The
menu snapshot runs first and then freezes autosave so those closing windows
cannot replace it.

If `~/.config/omarchy/extensions/omarchy-menu.jsonc` does not exist yet:

```bash
mkdir -p ~/.config/omarchy/extensions
cp ~/.config/omarchy/plugins/eric.session-restore/extensions/omarchy-menu-snippet.jsonc \
   ~/.config/omarchy/extensions/omarchy-menu.jsonc
omarchy menu refresh
```

If that file already exists, add the four keys from the snippet
(`system.session-save`, `system.logout`, `system.reboot`,
`system.shutdown`) inside the existing `{ }`. They override the stock
logout, reboot, and shutdown actions. Keep a single object: a second `{` or
a missing comma makes Omarchy ignore the whole extensions file. Then run
`omarchy menu refresh`.

The snippet uses `$HOME`, which the menu expands. If you already customized
those three system actions, put `omarchy-session save --final --quiet;` in
front of your command instead of replacing it.

You do not need to change `~/.bashrc` or `~/.zshrc`. The folder a terminal
reopens in is the interactive shell's directory, read from `/proc` at save
time. That includes Ghostty and Omarchy's floating terminal.

**Optional: Atuin session and Ghostty tabs.** If you want the same Atuin
history and the saved program started inside the new shell, install the
hook yourself. It is not part of the normal install and nothing writes it
for you:

```bash
omarchy-session install-hook
```

That adds one line to `~/.bashrc` (and `~/.zshrc` if you have one). New
shells pick it up; ones already open keep working as they are until you
restart them. Uninstall it with `omarchy-session uninstall-hook`.

### Update, pause, or remove

Update (Omarchy shows the diff before it applies):

```bash
omarchy plugin update eric.session-restore
```

Pause autosave and auto-restore, and leave the plugin installed:

```bash
omarchy-session disable
```

`omarchy plugin disable eric.session-restore`, or
**Setup → Plugins → Disable Plugin**, unloads the plugin.
Turn it back on with `omarchy-session enable` or
`omarchy plugin enable eric.session-restore`.

Remove:

```bash
omarchy-session uninstall-hook   # only if you installed the shell hook
omarchy plugin remove eric.session-restore
rm -f ~/.local/bin/omarchy-session
```

**Setup → Plugins → Remove Plugin** removes it the same way. If you merged
the menu snippet, delete those four keys from
`~/.config/omarchy/extensions/omarchy-menu.jsonc` and run
`omarchy menu refresh`. Saved sessions stay in
`~/.local/state/omarchy/session-restore`, and settings stay in
`~/.config/omarchy/session-restore.json`, until you delete them.

---

## Quick start

1. Install and enable (above), and say yes to the prompt.
2. Open a few apps and arrange your workspaces. Wait about a minute, or save now:

   ```bash
   omarchy-session save
   ```

   Without the short command:
   `~/.config/omarchy/plugins/eric.session-restore/bin/omarchy-session save`

3. Reboot or log out the way you usually do. With the menu rows installed,
   use **System → Reboot** (or Logout / Shutdown) so the last snapshot is
   taken as the windows close.
4. Log back in. The windows come back on their workspaces.

See what is saved, or what a restore would launch, without changing anything:

```bash
omarchy-session status
omarchy-session restore --dry-run
```

### Chrome: Continue where you left off

Browsers only reopen their tabs if the browser itself restores them. In
Chrome (and Chromium-family browsers):

**Settings → On startup → Continue where you left off**

Do that once per profile you care about. This plugin launches each profile
with `--profile-directory=…` and `--restore-last-session`.

A normal logout, and a reboot that Chrome records as `SessionEnded`, closes
windows one by one, so Chrome then remembers only the last window of each
profile. On every save that changes the window list, and on the final
pre-logout save, the plugin keeps a private copy of that profile's Chrome
session files and puts that copy back before launch. A crash is left alone —
Chrome's own file still has the full session.

Several Chrome profiles share one browser process, so neither the process
nor the window title says which profile a window belongs to. Each profile's
own session file does (`<profile>/Sessions/Session_*`, Chromium's "SNSS"
format). The plugin reads those files directly: every open window of every
profile, with its tabs in order and its selected tab. A Hyprland window is
tied to a Chromium window by its live title, which is always the selected
tab's title (unread counts ignored; windows that show the same title pair up
in the order they were opened). From that the save records each window's
profile and its list of tabs.
A terminal whose class is not the emulator's own (Omarchy's floating terminal
is `org.omarchy.terminal` on top of ghostty) is relaunched with `--class=`
so the new window is the one restore is waiting for.

On restore each profile is launched with `--profile-directory=…` (never
without one, which would open Chrome's profile picker). Once Chrome has
reopened its windows, the plugin reads the session files again and pairs
each saved window with the open window of the same profile that has the most
tabs in common (URLs, ignoring `#fragments` and New Tab pages; at least half
of the smaller window's tabs must match). Switching tabs, or a title that
changed since the last save, does not matter. Sessions saved before 1.4 have
no tab lists and are still matched by title. Chrome's profile picker is never
mistaken for a restored window; if one appears during restore it is closed.
If something is still missing after new windows stop appearing,
the plugin sends Chrome's reopen-closed-window shortcut (the same action as
History → recently closed), once per missing window.

Each window is placed by its name: the XDG tag when the app sets one,
otherwise the title Hyprland saw when the window was created (`initialTitle`),
otherwise the current title. Before launch, a temporary Hyprland rule opens
that named window on its saved workspace, so a late Chrome window does not
sit on workspace 1 until something moves it. The rule is removed when restore
finishes. A later pass moves any window whose name is recognizable but which
is still on the wrong workspace. The move is checked, and if the numeric
workspace id does not stick, it is retried with the workspace's name.

Tiled windows are then ordered left to right. On the scrolling layout each
window is given its own column; a directional "swap right" is not used,
because that dispatcher has no neighbor there and leaves the windows stacked.

---

## Why use it

- **One reboot, same desk.** Apps, workspaces, floating size/position,
  fullscreen, maximized, and pin come back without a restore wizard.
- **Terminals that feel continuous.** Each window returns in its working
  directory, read from the shell itself. The optional shell hook adds the
  same **Atuin** session and Ghostty **tabs**. A **coding agent** resumes
  into the same conversation (Claude, Codex, Grok, Cursor Agent, Gemini, …).
- **Multi-profile Chrome that just works.** Chromium-family browsers launch
  once per profile with `--profile-directory=…`, so the profile picker never
  interrupts restore. A clean logout no longer collapses each profile to its
  last window. Pair with Chrome → Settings → On startup →
  **Continue where you left off**.
- **Docked vs undocked layouts.** A separate layout is remembered for each
  display fingerprint (make/model/serial + geometry). Hotplug settles, then
  windows re-place themselves. First time on a new dock or USB-C display you
  arrange once; after that it is automatic.
- **Safe by default.** Atomic state files (mode 600), restore-at-most-once,
  dry-run mode, and optional menu rows that take a final snapshot before
  Omarchy closes windows for logout / reboot / shutdown.
- **Install in one command.** Public Git URL — no cloning required.

---

## Features

| Area | What you get |
|---|---|
| **Windows** | Apps relaunched on the workspaces they were on; floating geometry, fullscreen, maximized, pin |
| **Terminals** | ghostty (including `org.omarchy.terminal`), kitty, alacritty, foot, wezterm, and any `TerminalEmulator` — the shell's cwd, no shell rc changes; optional Atuin session + tabs + agent resume |
| **Browsers** | Chrome / Chromium / Brave / Edge / Vivaldi / … once per profile; Firefox-family once; web apps via `.desktop` / `--app=` |
| **Other apps** | Flatpak, AppImage, and argv from `/proc` — multi-window apps launch once, extras matched by title |
| **Per-display** | Fingerprint-keyed layouts under `~/.local/state/omarchy/session-restore/layouts/` |
| **Autosave** | Every 60 s and ~3 s after window changes; skipped while the system is stopping |
| **Menu** | Optional: Save Session, plus Logout / Reboot / Shutdown that snapshot first |
| **CLI** | `status`, `save`, `restore --dry-run`, `--force`, `--prev`, disable/enable |

---

## What gets restored

| Kind | Detection | Restore behavior |
|---|---|---|
| **Terminals** | process / class table + `TerminalEmulator` desktop category | One window per saved window. The directory is `/proc/<shell>/cwd` of the interactive shell that is the terminal's direct child — not vim, ssh, or an agent. Several Ghostty windows in one process are paired with those shells in start order. If a window cannot be paired, a fresh hook directory is used when it identifies exactly one folder, otherwise `$HOME`. Known TUIs relaunch; coding agents resume. The shell hook is optional and only adds the Atuin session and tab handoff. |
| **Browsers** | `WebBrowser` desktop category / binary table | Chromium-family: **once per profile** with `--profile-directory=…`. A pre-logout session snapshot is restored after a clean exit. Firefox-family: once. Windows moved to saved workspaces by title. |
| **Web apps** | `chrome-<site>-Default`-style classes | Via `.desktop` (`StartupWMClass`), else `--app=URL`, else URL from class. |
| **Everything else** | `/proc/<pid>/cmdline`, flatpak cgroup, `$APPIMAGE`, `.desktop` | Same argv / `flatpak run` / AppImage / desktop `Exec`. Multi-window apps launch once; extras matched by title. |

Floating state, size/position (floating windows), fullscreen/maximized and
pin are re-applied. Per-workspace layout mode (dwindle / scrolling / floating)
is restored when Omarchy’s `o.workspace_mode` is available. Windows on special
(scratchpad) workspaces are saved/restored when `restore_special` is true
(default).

### Per-display layouts (docked vs undocked)

A **separate window layout is remembered for each display configuration**,
like macOS. The fingerprint is the sorted list of connected monitors
identified by make/model/serial (Hyprland’s `description` — the same identity
Omarchy uses for workspace blocks) plus resolution, scale and relative
position — not the connector name (`HDMI-A-1`), which a dock can rename.

Layouts live under `~/.local/state/omarchy/session-restore/layouts/<hash>/`
and are never consumed on restore, so docking again can find them. On monitor
hotplug the daemon waits `monitor_settle_seconds` (default 3), saves the
previous layout, then re-places already-open windows to match the layout for
the new fingerprint when one exists. A **brand-new** display config (first
time on that dock or portable display) gets Hyprland’s defaults until you
arrange windows and a save runs.

### Coverage vs Hyprland

| Feature | Support | Notes |
|---|---|---|
| App launch + workspace | **full** | terminals (cwd/Atuin/tabs/agents), browsers (per Chrome profile), web apps, other apps |
| Floating / tiled | **full** | floating flag toggled on restore |
| Floating size + position | **full** | clamped onto a live monitor if the saved display is gone |
| Fullscreen / maximized | **full** | |
| Pin (all workspaces) | **full** | Hyprland pin; not macOS-style edge snap |
| Monitor placement | **full** | workspace moved onto the matching physical monitor by identity |
| Per-display layouts | **full** | fingerprint-keyed; hotplug settle + relayout |
| Workspace layout mode | **partial** | dwindle / scrolling / floating via `o.workspace_mode`. Tiled windows are ordered left to right (scrolling: one column each). **Exact dwindle split tree is not exposed by Hyprland** |
| Scrolling column widths | **unsupported** | hyprscrolling options are global; per-column widths not in IPC |
| Special / scratchpad | **partial** | saved/restored by name (`special:scratchpad`); may interact with Omarchy qconsole |
| Window groups | **unsupported** | `grouped` count is recorded; membership is not rebuilt |

There is **no** native Hyprland “layout dump.” Everything goes through
`hyprctl -j` plus this plugin’s own session JSON.

---

## Terminals: directories, and the optional hook

No shell rc change is required. At save time each terminal window's pid
comes from Hyprland. The interactive shell that is that process's direct
child (bash, zsh, fish, and the other shells the plugin already knows) is
the one whose `/proc/<pid>/cwd` is stored. That is the folder you `cd`'d
into, even when vim, ssh, or an agent is running in front of it. Ghostty
windows that share one process, including Omarchy's floating
`org.omarchy.terminal`, are matched to those shells in the order they
started. A unique directory in the window title can break a tie. If a
window still cannot be matched, or `/proc` cannot be read, a fresh hook
file is used only when it names exactly one directory; otherwise the
terminal reopens in your home directory.

The hook is optional. Install it only for the same Atuin session and for
Ghostty tabs that claim their saved state:

```bash
omarchy-session install-hook
```

It adds one line to `~/.bashrc` (and `~/.zshrc` if present) right after
`atuin init`, with a backup:

```bash
[ -f ~/.config/omarchy/plugins/eric.session-restore/shell/session-hook.sh ] && . ~/.config/omarchy/plugins/eric.session-restore/shell/session-hook.sh  # omarchy-session-restore hook
```

At shell start the hook records `$ATUIN_SESSION` and `$PWD` under
`$XDG_RUNTIME_DIR/omarchy-session-restore/` (mode 600). The directory there
is a fallback, not the normal source. When a restore opened the terminal,
the hook claims that tab’s saved state: `cd`, `export ATUIN_SESSION=…`,
and the program to resume at the first prompt so the shell stays open after
it exits. Values are validated and shell-quoted.

**Atuin.** Reusing a session id is safe — Atuin stores it as a plain column
with no uniqueness rule. The session filter (Ctrl-R, cycle filter mode) shows
that window’s commands from before the reboot. Optional:
`filter_mode_shell_up_key_binding = "session"` for per-window up-arrow.

**Tabs.** Ghostty tabs come back via D-Bus (`new-tab`) with each tab’s cwd,
Atuin session and program. Splits come back as tabs (split layout isn’t
readable from outside). Other terminals get extra tabs as separate windows on
the same workspace.

**Coding agents.** Covers claude, codex, grok, cursor-agent, gemini, opencode,
kimi, and many others (binary, mise/npm shim, or `node …/cli.js`). Session id
from live state, original argv, or newest transcript — otherwise the agent’s
own “continue latest” (`claude --continue`, `codex resume --last`, …).
Permission-skipping flags are never added; one-shot runs (`claude -p`, …) are
not restarted; no prompt is ever sent. Agents inside herdr are left to herdr.

Without the hook, terminals still return in the shell's folder with the
program and agent resumed, but each gets a new Atuin session, and a Ghostty
window's extra tabs open as separate windows on the same workspace.

**Not restored.** Windows running a one-shot command — Omarchy's floating
update or install window (`bash -c 'omarchy-update …'`), or any terminal
started with `-e <script>` — are not saved; relaunching them would only leave
an empty floating shell. Tabs that attach to the same persistent session
(`herdr`, `tmux new -A -s …`, `zellij attach …`) come back once, not once per
tab, since every copy would show the same session.

---

## How it works

* `Service.qml` (headless omarchy-shell service) runs `bin/omarchy-session daemon`.
* On start the daemon **restores once**, then **autosaves** every 60 s and
  ~3 s after window open/close/move/float/fullscreen events.
* With the optional menu snippet, Logout / Reboot / Shutdown run `omarchy-session save --final` first
  (exact final snapshot; freezes autosave for 2 minutes so Omarchy’s “close
  all windows” step cannot overwrite it), then the stock `omarchy-system`
  command.
* Launch commands are computed **at save time** (while `/proc` still knows
  everything) and stored as argv lists. Restore never runs a saved string
  through `sh -c`.

### Safety

* State in `~/.local/state/omarchy/session-restore/` (mode 700);
  `session.json` is mode 600, written atomically; previous distinct version
  kept as `session.prev.json`.
* Restored **at most once**: moved to `restored/` before launch; hash in
  `last-restore.json`.
* Skipped if saved by the *current* Hyprland session, older than
  `max_age_hours` (default 7 days), or Hyprland has been up longer than
  15 minutes.
* Apps already open (e.g. autostart) are claimed, not double-launched.

---

## Usage

```bash
omarchy-session status              # daemon, saved session, last restore
omarchy-session save                # save now (also: System → Save Session, after the menu snippet)
omarchy-session restore --dry-run   # print what would launch (alias --print)
omarchy-session restore --force     # restore now even if checks would skip
omarchy-session restore --prev      # previous good copy
omarchy-session restore --file F    # specific file (not consumed)
omarchy-session restore --file F --workspace 4
omarchy-session install-hook        # optional: Atuin session + tab handoff (not required for directories)
omarchy-session uninstall-hook        # only if you installed that hook
omarchy-session disable | enable
```

Log: `~/.local/state/omarchy/session-restore/session-restore.log`

### Optional config — `~/.config/omarchy/session-restore.json`

```json
{
  "enabled": true,
  "max_age_hours": 168,
  "max_login_age_seconds": 900,
  "save_interval_seconds": 60,
  "browser_wait_seconds": 150,
  "browser_settle_seconds": 12,
  "browser_primary_wait_seconds": 15,
  "restore_chromium_session": true,
  "preserve_crashed": true,
  "quit_browsers_on_shutdown": true,
  "skip_classes": ["org.pulseaudio.pavucontrol"],
  "resume_commands": ["herdr", "tmux", "zellij", "nvim", "btop", "lazygit", "yazi"],
  "notify": true,
  "resume_agents": true,
  "per_display": true,
  "restore_special": true,
  "monitor_settle_seconds": 3
}
```

| Key | Default | Meaning |
|---|---|---|
| `enabled` | `true` | Autosave + auto-restore |
| `max_age_hours` | `168` | Don’t restore sessions older than this |
| `max_login_age_seconds` | `900` | Only auto-restore this soon after Hyprland starts |
| `save_interval_seconds` | `60` | Periodic autosave interval |
| `browser_wait_seconds` | `150` | Cap on how long to wait for browser windows. Restore returns as soon as every saved window has matched. While new windows are still appearing the cap can stretch by half again |
| `browser_settle_seconds` | `12` | Quiet period with no new windows before reopening a missing Chrome window |
| `browser_primary_wait_seconds` | `15` | When several profiles of one Chromium browser are restored, wait up to this long for the first profile's browser process before launching the others |
| `restore_chromium_session` | `true` | After a clean Chrome exit, restore the pre-logout session snapshot so every window comes back |
| `preserve_crashed` | `true` | If an app crashes (fatal signal, coredump, or a non-zero exit) and its windows disappear, keep those windows in the saved session until the app is opened again or you close it normally |
| `quit_browsers_on_shutdown` | `true` | Hold a logind delay lock and, when any reboot or poweroff starts, ask Chromium-family browsers to quit cleanly (bounded by logind's `InhibitDelayMaxSec`) |
| `skip_classes` | `[]` | Window classes never saved (full-match regexes) |
| `resume_commands` | *(built-in TUI list)* | Foreground programs to relaunch in terminals |
| `notify` | `true` | Desktop notifications on restore |
| `resume_agents` | `true` | Resume coding agents into their conversation |
| `per_display` | `true` | Separate layout per display fingerprint |
| `restore_special` | `true` | Save/restore special/scratchpad workspaces |
| `monitor_settle_seconds` | `3` | Delay after monitor hotplug before switching layouts |

---

## Limitations (honest)

* **Dwindle split tree** — Hyprland does not expose the exact split tree over
  IPC. Workspace *mode* (dwindle / scrolling / floating) is restored; exact
  split ratios are not. Tiled windows are ordered left to right (on the
  scrolling layout, each in its own column). If the layout still disagrees,
  drag one past the other once.
* **Scrolling column widths** — hyprscrolling column widths are not in IPC.
* **First time on a new dock / display** — no saved layout yet; arrange once,
  then autosave remembers it for next time.
* **Browsers** need their own session restore (Chrome: *Continue where you
  left off*). Chromium-family windows are matched by their tabs, read from
  the browser's session files; Firefox-family windows by title. An encrypted
  Chromium session file cannot be read; those windows fall back to the
  last-used profile and title matching. After a clean
  exit the plugin restores Chrome's pre-logout session so windows the logout
  close dropped are not lost; turn that off with `restore_chromium_session`.
* **Terminal scrollback** and arbitrary running processes are not preserved —
  only the shell's folder, an Atuin session (only if you installed the
  optional hook), known TUIs, and coding-agent conversations.
* **Ghostty splits** come back as tabs; tab-to-window assignment is based on
  shell start times. Ghostty restored windows run with
  `--gtk-single-instance=false` so `--working-directory` is honored.
* **In-app documents** reopen however the app normally does, unless they were
  on the original command line.
* A hard power-off still restores the last autosave (≤ 60 s old). Logging out
  via `uwsm stop` / a keybinding instead of the menu skips the final snapshot.
  Reboot and poweroff from anywhere (menu, `omarchy update`'s reboot prompt,
  `systemctl reboot`) still let Chromium quit cleanly through the shutdown
  guard; a plain logout does not, since logind is not involved.

---

## Recent changes

### 1.4.6
- If an app crashes and its windows disappear, those windows stay in the
  saved session until the app is opened again or you close it normally.
  A close while the process is still running, or a clean exit (including
  SIGTERM, which the shutdown guard uses), still drops them.
- The earlier Chrome-only guard refused a whole save when every Chrome
  window vanished, which is why a mid-session Chrome crash was already
  restored after a reboot. That keep is now per-app, so a crash no longer
  blocks later changes to the rest of the desk from being saved. The
  plugin treats a window as crashed when its process is already gone at
  the moment the window disappears (SIGKILL, oom, or a fatal signal). A
  close while the process is still running, then a normal exit, is left
  out of the session. Chromium's `exit_type=Crashed` covers a crash even
  when the process was not yet being watched.

### 1.4.5
- Installed web apps (`--app-id` PWAs) and `--app` windows are always
  launched with their own `--profile-directory`, also for `Default`.
  Without it, a browser already running another profile opened the app in
  that profile, where it is not installed, and no window appeared. A web app
  whose profile is still waiting for its deferred browser launch now starts
  after that launch, so it cannot open the profile without its session.
- A second Chrome profile that comes up as a New Tab window no longer
  gives up on Ctrl+Shift+T after one try because no window could be told
  apart yet. Restore keeps waiting until the deadline, and a New Tab that
  first appeared after that profile's own launch is taken as its stand-in
  right away. Before, that profile's window stayed empty.
- The title fallback no longer rejects an exact title match because a
  shared word (for example a domain-like word in a repo path) appears in
  another profile's tab. Another profile now blocks the match only when it
  fits at least as well. The reopened window is then paired, and the empty
  New Tab stand-in is closed as intended.

### 1.4.4
- Chrome no longer comes back with "Chrome didn't shut down correctly" and a
  Restore button that duplicates the restored window. The reboot prompt at
  the end of `omarchy update` calls `omarchy-system reboot` directly, so the
  menu rows' `save --final` (which asks Chrome to quit) never ran. Omarchy
  then closes windows for at most 2 seconds before rebooting, which a large
  Chrome does not finish, and a profile was left marked as crashed.
- Shutdown guard: the daemon holds a logind delay lock. When any reboot or
  poweroff starts, it sends Chromium-family browsers SIGTERM (Chrome treats
  that as a session end and keeps every window), waits until each profile
  records a clean exit, then releases the lock. It runs in its own thread
  and is bounded by logind's `InhibitDelayMaxSec`. Turn it off with
  `quit_browsers_on_shutdown`.
- Safety net at restore: after the session to restore has been chosen, and
  only while no browser is running for that user-data directory, a profile
  still marked as crashed is set back to a normal exit in its `Preferences`
  (`exit_type`, `exited_cleanly`; nothing else). Restore already reopens
  those windows, so Chrome's own restore bubble could only add duplicates.

### 1.4.3
- Title fallback for a Chrome window missing from the session files no
  longer runs the instant the window appears. Tab-set matching stays the
  primary path: the fallback waits until those files have been read and a
  short grace has passed, so a slow session-file write cannot be claimed
  by the current tab's title. The match itself must be a unique,
  distinctive title (the saved window title or any of its tab titles) in
  the same profile. Short or generic names such as "jay", "New Tab", or
  "Inbox", and two windows with similar titles, are left unmoved rather
  than guessed.

### 1.4.2
- Restore no longer waits out the full browser timeout to place a Chrome
  window that is already on screen but missing from Chromium's session
  files. Those windows are matched by title as soon as they are visible,
  instead of only when the wait expires. On a three-window desk this was
  most of a two-and-a-half-minute restore.
- The second Chrome profile is not launched in the middle of the item
  loop, so terminals and other apps start as soon as the first profile
  has started the browser. If that first launch already opened the other
  profile's windows, the second launch is skipped. Session files are
  still never copied under a live browser.
- Quieter, shorter waits: settle 4s (was 12s), reopen after about 15s
  (was 45s), and a 60s cap (was 150s), with an early finish once windows
  have settled and reopen has had its chance.

### 1.4.1
- Terminal windows are no longer swapped on restore just because every
  Ghostty window starts with the initial title "Ghostty". That name is
  treated as generic, so two terminals are paired by their real titles
  (for example a TUI on workspace 1 and a shell on workspace 3).
- Chrome session snapshots for every profile are installed before the
  browser process starts. 1.4.0 copied the second profile's Session
  files after the first profile had already launched, which raced with
  Chromium, dropped the other profile's tabs, and could crash Chrome.
  If a later profile's windows appear from that first launch, it is not
  launched again.
- An automatic save no longer overwrites a session that still has Chrome
  windows with one that has none, so a mid-restore Chrome crash does not
  become the layout used on the next login.

### 1.4.0
- Chrome windows are identified by their set of tabs, not by their title.
  The plugin now parses each profile's Chromium session file (SNSS) to get
  every open window with its tabs, and uses that to tell which profile a
  window belongs to. The old way grepped title-like strings out of those
  files and scored them, so a short title such as a three-letter site name
  could not be placed in a profile; that window was then saved without one,
  and restoring it opened Chrome's profile picker.
- `session.json` format 2: each saved Chrome window has an id (`w1`, `w2`,
  …), its profile, and its tab URLs and titles. Restore pairs windows by tab
  overlap within a profile. Format 1 files still load and match by title.
- A Chromium window is never saved or launched without a profile. A window
  that is not in any session file yet keeps what the previous save found, or
  goes to Local State's last-used profile.
- The profile picker is never claimed as a New Tab stand-in, and is closed
  if it appears during restore. A stand-in must belong to the right profile.
- `restore --dry-run` shows, for each saved Chrome window, how many tabs it
  has and which open window it would pair with now.

### 1.3.9
- The leftover New Tab stand-in is actually closed now. 1.3.7 sent
  Hyprland's old `closewindow address:…` dispatcher, which the Lua dispatcher
  rejects, so an empty New Tab window stayed open next to the restored one.

### 1.3.8
- Several profiles of one Chromium browser are no longer launched at the
  same instant. Only the profile that starts the browser process gets
  `--restore-last-session`; the others are handed to the running process and
  open a New Tab. The profile with the most saved windows now starts first,
  and the rest launch once its process is up, so which profile restores
  natively is no longer a race.
- A New Tab / What's New placeholder is no longer treated as a saved window
  just because every Chromium window starts out titled "New Tab". It stays
  free to become that profile's stand-in.
- Ctrl+Shift+T never targets a window placed for another profile. Profiles
  share one browser PID, so the same-PID fallback could reopen a closed tab
  in the wrong profile's window.

### 1.3.7
- After saved windows have been reopened, a leftover New Tab / What's New
  stand-in is closed. If that placeholder's title has changed to real
  content, it is left alone. The stand-in is not counted as a restored
  window.

### 1.3.6
- On **Logout / Reboot / Shutdown** (`save --final`), Chromium-family browsers
  are asked to quit cleanly before Omarchy closes windows, so profiles record
  a normal exit and the pre-logout session snapshot can be installed on the
  next login instead of Chrome's crash-restore bubble.
- Ctrl+Shift+T reopen waits longer while `--restore-last-session` is still
  opening windows, and never fires within a few seconds of a profile's first
  window — avoiding duplicate tabs/windows after a crashy exit.
- A New Tab / What's New placeholder for a profile with unmatched saved
  windows is claimed as that profile's stand-in, moved to the saved
  workspace, and used as the reopen target when title matching would fail.

## Attribution & license

Derived from
[wbarakat/omarchy-session-restore](https://github.com/wbarakat/omarchy-session-restore)
(MIT, © 2026 Waleed) — rewritten in Python with generic app detection, atomic
state, restore-once guarantees, dry-run mode, per-profile Chrome launch, and
per-display layouts. See `LICENSE`.

MIT © 2026 Waleed and Eric Westphal.

Questions / bugs: open an issue at
[github.com/westphae/omarchy-session-restore](https://github.com/westphae/omarchy-session-restore)
