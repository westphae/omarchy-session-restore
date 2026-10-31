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
| **Version** | 1.3.2 |
| **License** | MIT |
| **Author** | Eric Westphal &lt;BonanzaEric@gmail.com&gt; |
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

**3. Shell hook, for terminal continuity.** Each terminal comes back with
the same Atuin history and Ghostty tabs, and a resumed program stays inside
the shell. Without the hook, terminals still reopen in the right folder,
with their program and coding agent, but each gets a new Atuin session and
a single tab. Bash and zsh only.

```bash
omarchy-session install-hook
```

That needs step 1. New terminals pick the hook up; ones already open keep
working as they are until you restart them.

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

A normal logout closes Chrome's windows one by one, and Chrome then remembers
only the last window of each profile. On every save that changes the window
list, and on the final pre-logout save, the plugin keeps a private copy of
that profile's Chrome session files. After a **clean** exit it puts that copy
back before launch, so every window comes back. A crash is left alone —
Chrome's own file still has the full session.

Windows are matched to workspaces by title. Unread counts and a shortened
tab title (`JLCPCB`, `Gmail`) still match, and each profile only takes its
own windows. If something is still missing after new windows stop appearing,
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
  directory; with the optional shell hook you also get the same **Atuin
  session**, Ghostty **tabs**, and a **coding agent** resumed into the same
  conversation (Claude, Codex, Grok, Cursor Agent, Gemini, …).
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
| **Terminals** | ghostty, kitty, alacritty, foot, wezterm, and any `TerminalEmulator` desktop entry — cwd restored; optional Atuin session + tabs + agent resume |
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
| **Terminals** | process / class table + `TerminalEmulator` desktop category | One window per saved window, with that terminal’s working-directory flag (or `env -C` / `xdg-terminal-exec --dir`). Known TUIs (herdr, tmux, zellij, nvim, btop, lazygit, yazi, …) relaunch; coding agents resume the same conversation. With the shell hook: Atuin session + tabs. |
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

## Terminals: Atuin, tabs, coding agents

Run `omarchy-session install-hook` once. It adds one line to `~/.bashrc`
(and `~/.zshrc` if present) right after `atuin init`, with a backup:

```bash
[ -f ~/.config/omarchy/plugins/eric.session-restore/shell/session-hook.sh ] && . ~/.config/omarchy/plugins/eric.session-restore/shell/session-hook.sh  # omarchy-session-restore hook
```

At shell start the hook records `$ATUIN_SESSION` under
`$XDG_RUNTIME_DIR/omarchy-session-restore/` (mode 600). When a restore opened
the terminal, it claims that tab’s saved state: `cd`, `export ATUIN_SESSION=…`,
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

Without the hook, terminals still return in the right folder with program and
agent resumed, but each gets a new Atuin session and only one tab.

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
omarchy-session install-hook        # Atuin + tabs + agents
omarchy-session uninstall-hook
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
  "restore_chromium_session": true,
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
| `restore_chromium_session` | `true` | After a clean Chrome exit, restore the pre-logout session snapshot so every window comes back |
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
  left off*). Titles are used to match windows to workspaces. After a clean
  exit the plugin restores Chrome's pre-logout session so windows the logout
  close dropped are not lost; turn that off with `restore_chromium_session`.
* **Terminal scrollback** and arbitrary running processes are not preserved —
  only folder, Atuin session (with hook), known TUIs, and coding-agent
  conversations.
* **Ghostty splits** come back as tabs; tab-to-window assignment is based on
  shell start times. Ghostty restored windows run with
  `--gtk-single-instance=false` so `--working-directory` is honored.
* **In-app documents** reopen however the app normally does, unless they were
  on the original command line.
* A hard power-off still restores the last autosave (≤ 60 s old). Logging out
  via `uwsm stop` / a keybinding instead of the menu skips the final snapshot.

---

## Attribution & license

Derived from
[wbarakat/omarchy-session-restore](https://github.com/wbarakat/omarchy-session-restore)
(MIT, © 2026 Waleed) — rewritten in Python with generic app detection, atomic
state, restore-once guarantees, dry-run mode, per-profile Chrome launch, and
per-display layouts. See `LICENSE`.

MIT © 2026 Waleed and Eric Westphal.

Questions / bugs: BonanzaEric@gmail.com ·
[github.com/westphae/omarchy-session-restore](https://github.com/westphae/omarchy-session-restore)
