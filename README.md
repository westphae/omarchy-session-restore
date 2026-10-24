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
| **Version** | 1.3.0 |
| **License** | MIT |
| **Author** | Eric Westphal &lt;BonanzaEric@gmail.com&gt; |
| **Based on** | [wbarakat/omarchy-session-restore](https://github.com/wbarakat/omarchy-session-restore) (MIT, © 2026 Waleed) |

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
  interrupts restore. Pair with Chrome → Settings → On startup →
  **Continue where you left off**.
- **Docked vs undocked layouts.** A separate layout is remembered for each
  display fingerprint (make/model/serial + geometry). Hotplug settles, then
  windows re-place themselves. First time on a new dock or USB-C display you
  arrange once; after that it is automatic.
- **Safe by default.** Atomic state files (mode 600), restore-at-most-once,
  dry-run mode, and menu rows that take a final snapshot before Omarchy closes
  windows for logout / reboot / shutdown.
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
| **Menu** | Save Session, plus Logout / Reboot / Shutdown that snapshot first |
| **CLI** | `status`, `save`, `restore --dry-run`, `--force`, `--prev`, disable/enable |

---

## Install

Requires Omarchy 4.5+ with the plugin system.

```bash
omarchy plugin add https://github.com/westphae/omarchy-session-restore.git --enable
```

Then put the CLI on your `PATH` and (optionally) wire the menu + shell hook:

```bash
ln -sf ~/.config/omarchy/plugins/eric.session-restore/bin/omarchy-session ~/.local/bin/omarchy-session

# Optional: final snapshot before logout / reboot / shutdown
# Merge extensions/omarchy-menu-snippet.jsonc into
# ~/.config/omarchy/extensions/omarchy-menu.jsonc, then:
omarchy menu refresh

# Optional: per-window Atuin sessions, Ghostty tabs, coding-agent resume
omarchy-session install-hook
```

Update later:

```bash
omarchy plugin update eric.session-restore
```

Disable without removing: `omarchy-session disable` (or
`omarchy plugin disable eric.session-restore`).

Remove completely:

```bash
omarchy-session uninstall-hook   # if you installed the hook
omarchy plugin remove eric.session-restore
rm -f ~/.local/bin/omarchy-session
# delete the four session rows from ~/.config/omarchy/extensions/omarchy-menu.jsonc
omarchy menu refresh
rm -rf ~/.local/state/omarchy/session-restore ~/.config/omarchy/session-restore.json
```

---

## Quick start

1. Install and enable (above).
2. Open a few apps, rearrange workspaces, wait ~60 s (or run
   `omarchy-session save`).
3. Reboot from the Omarchy menu (so the final snapshot runs).
4. After login, windows come back on their workspaces.

Check status anytime:

```bash
omarchy-session status
omarchy-session restore --dry-run   # print what would launch; change nothing
```

### Chrome: Continue where you left off

Browsers only reopen their tabs if the browser itself restores them. In
Chrome (and Chromium-family browsers):

**Settings → On startup → Continue where you left off**

Do that once per profile you care about. This plugin launches each profile
correctly; Chrome restores the tabs inside those windows.

---

## What gets restored

| Kind | Detection | Restore behavior |
|---|---|---|
| **Terminals** | process / class table + `TerminalEmulator` desktop category | One window per saved window, with that terminal’s working-directory flag (or `env -C` / `xdg-terminal-exec --dir`). Known TUIs (herdr, tmux, zellij, nvim, btop, lazygit, yazi, …) relaunch; coding agents resume the same conversation. With the shell hook: Atuin session + tabs. |
| **Browsers** | `WebBrowser` desktop category / binary table | Chromium-family: **once per profile** with `--profile-directory=…`. Firefox-family: once. Windows moved to saved workspaces by title. |
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
| Workspace layout mode | **partial** | dwindle / scrolling / floating via `o.workspace_mode`; **exact dwindle split tree is not exposed by Hyprland** |
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
* Menu Logout / Reboot / Shutdown run `omarchy-session save --final` first
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
omarchy-session save                # save now (also: menu → System → Save Session)
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
  "browser_wait_seconds": 60,
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
| `browser_wait_seconds` | `60` | How long to wait for browser windows to appear |
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
  split ratios are not. Tiled windows are re-ordered left-to-right; if the
  layout still disagrees, drag one past the other once.
* **Scrolling column widths** — hyprscrolling column widths are not in IPC.
* **First time on a new dock / display** — no saved layout yet; arrange once,
  then autosave remembers it for next time.
* **Browsers** need their own session restore (Chrome: *Continue where you
  left off*). Titles are used to match windows to workspaces/profiles.
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
