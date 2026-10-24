# Session Restore for Omarchy (`eric.session-restore`)

An Omarchy 4.5 plugin that remembers your open windows and puts them back
after a reboot, logout or crash: same apps, same workspaces, terminals in the
same folders.

Derived from [wbarakat/omarchy-session-restore](https://github.com/wbarakat/omarchy-session-restore)
(MIT, © 2026 Waleed) — rewritten in Python with generic app detection,
atomic state, restore-once guarantees and a dry-run mode. See `LICENSE`.

## What gets restored

| Kind | How it's detected | How it comes back |
|---|---|---|
| **Terminals** (ghostty, kitty, alacritty, foot, wezterm, konsole, gnome-terminal, kgx, ptyxis, xfce4-terminal, tilix, terminator, rio, urxvt, st, xterm, contour, or anything whose `.desktop` file says `TerminalEmulator`) | process name / window class table + desktop categories | one window per saved window, launched with that terminal's own working-directory flag (or `env -C`, or `xdg-terminal-exec --dir` for an unknown default terminal). If a known TUI was in the foreground (herdr, tmux, zellij, nvim, btop, lazygit, yazi, …) it is started again, and you drop back to your shell when it exits. A **coding agent** (claude, codex, grok, cursor-agent, gemini, kimi, opencode, …) is resumed into the same conversation. With the shell hook, each window also gets back its **Atuin session** and its **tabs** (see below). |
| **Browsers** (Chrome, Chromium, Brave, Edge, Vivaldi, Opera, Helium, Thorium, Firefox, LibreWolf, Zen, Floorp, Waterfox, … or any `WebBrowser` desktop entry) | desktop category / binary table | Chromium-family browsers are launched **once per profile** with `--profile-directory=…` (skips the profile picker when several profiles were open). Each profile reopens its own windows, then windows are moved to their saved workspaces by matching titles. Firefox-family browsers still launch once. |
| **Web apps** (`chrome-<site>-Default` style classes from `omarchy-launch-webapp` / `--app=`) | window class pattern | each one individually, via its `.desktop` file (`StartupWMClass`), else `--app=URL` from the process, else a URL rebuilt from the class. |
| **Everything else** | `/proc/<pid>/cmdline`, flatpak cgroup, `$APPIMAGE`, `.desktop` file lookup | relaunched with the same argv (or `flatpak run`, the AppImage, or the desktop `Exec`). Multi-window apps launch once; extra windows are matched by title. |

Floating state, size/position (floating windows), fullscreen/maximized and
pin are re-applied. Windows on special (scratchpad) workspaces are skipped.

## Terminals: Atuin sessions, tabs and coding agents

Run `omarchy-session install-hook` once. It adds one line to `~/.bashrc`
(and `~/.zshrc` if present) right after `atuin init`, with a backup:

```
[ -f ~/.config/omarchy/plugins/eric.session-restore/shell/session-hook.sh ] && . ~/.config/omarchy/plugins/eric.session-restore/shell/session-hook.sh  # omarchy-session-restore hook
```

`shell/session-hook.sh` is small. At shell start it records `$ATUIN_SESSION`
in `$XDG_RUNTIME_DIR/omarchy-session-restore/shell-<pid>` (mode 600). Atuin
picks its session id inside the shell, so `/proc/<pid>/environ` never shows
it. When a restore opened the terminal, the hook asks `omarchy-session
claim-tab` for that tab's saved state and applies it: `cd`, `export
ATUIN_SESSION=…`, and the program to resume, which runs at the first prompt
so the shell stays open after it exits. All values are validated and
shell-quoted.

**Atuin.** Reusing a session id is safe. Atuin stores the session as a
plain column on each history row, with no uniqueness rule, so a restored
window keeps adding to the same session. Its *session* filter (Ctrl-R, then
cycle the filter mode) shows that window's commands from before the reboot.
Your `filter_mode` is not changed. If you use Atuin's up-arrow binding,
`filter_mode_shell_up_key_binding = "session"` makes up-arrow per-window too.

**Tabs and splits.** Ghostty doesn't say which window a shell belongs to.
Leftover shells (tabs and splits) are attached to the window whose first
shell started most recently before them. On restore, Ghostty windows get their
tabs back through Ghostty's D-Bus window actions (`new-tab`), with each tab's
own cwd, Atuin session and program. Ghostty only acts on the focused window,
so the restored window is focused briefly and focus goes back afterwards.
Splits come back as tabs, because the split layout can't be read from
outside. kitty, wezterm and other terminals get their extra tabs as separate
windows on the same workspace.

**Coding agents.** `AGENTS` in `bin/omarchy-session` covers claude, codex,
grok, cursor-agent, gemini, opencode, kilo, kimi, qwen, copilot, droid,
devin, qodercli, hermes, pi, omp, agy, letta, mastracode, crush, aider,
goose and amp, whether they run as a binary, through mise/npm shims or as
`node …/cli.js`. The session id is found in this order:

1. live state: `~/.grok/active_sessions.json`, `~/.claude/sessions/<pid>.json`,
   or the transcript file the agent has open (codex rollouts, cursor chats,
   kimi sessions, …);
2. the original command line (`--resume ID`, `codex resume ID`, …);
3. for claude, the newest transcript for that directory.

If no id is found, the agent's own "continue latest in this directory" is
used, e.g. `claude --continue` or `codex resume --last`. An agent that never
had a conversation (grok with no registered session) is started fresh rather
than continuing an older conversation in that directory. Model and permission
flags are copied from the original command only when they were there.
Permission-skipping flags such as `--dangerously-skip-permissions` or `--yolo`
are never added. One-shot runs (`claude -p`, `codex exec`, …) are not
restarted, and no prompt is ever sent. Agents inside herdr are resumed by
herdr's own session restore; the plugin only reattaches herdr.

Without the hook, terminals still come back in the right folder with their
program and agent resumed, but each gets a new Atuin session and only one tab.

## How it works

* `Service.qml` (a headless omarchy-shell service) runs
  `bin/omarchy-session daemon`.
* On start the daemon **restores once**, then **autosaves**: every 60 s and
  ~3 s after window open/close/move/float/fullscreen events.
* The reboot / shutdown / logout menu rows run
  `omarchy-session save --final` first (an exact final snapshot that also
  freezes autosave for 2 minutes so Omarchy's "close all windows" step can't
  overwrite it), then the stock `omarchy-system` command.
* Autosave also refuses to write while the system is stopping, while an
  `omarchy-system reboot|shutdown|logout` is running, or when there are no
  windows at all.

Launch commands are worked out **at save time** (while `/proc` still knows
everything) and stored as argv lists. Restore never runs a saved string
through `sh -c`: argv is shell-quoted with `shlex` and handed to Hyprland's
`hl.dsp.exec_cmd` with a `[workspace N silent]` rule, then the window is
moved to its workspace by address in case the app handed off to an existing
process.

### Safety

* State lives in `~/.local/state/omarchy/session-restore/` (mode 700);
  `session.json` is mode 600, written atomically (temp file + fsync +
  rename), and the previous distinct version is kept as `session.prev.json`.
  Files that aren't yours or are group/world-writable are refused.
* A session is restored **at most once**: it is moved to `restored/` before
  anything launches, and its hash is recorded in `last-restore.json`.
* Not restored if: it was saved by the *current* Hyprland session (so
  restarting omarchy-shell does nothing), it's older than `max_age_hours`
  (default 7 days), or Hyprland has been up longer than 15 minutes.
* Apps that are already open (e.g. autostarted) are claimed instead of
  launched a second time; a browser that is already running is not launched.

## Usage

```
omarchy-session status              # daemon, saved session, last restore
omarchy-session save                # save now (also: menu → System → Save Session)
omarchy-session restore --dry-run   # print exactly what would be launched (alias --print)
omarchy-session restore --force     # restore now even if the checks would skip it
omarchy-session restore --prev      # use the previous good copy
omarchy-session restore --file F    # restore a specific file (not consumed)
omarchy-session restore --file F --workspace 4   # only the windows saved on workspace 4
omarchy-session install-hook        # per-window Atuin sessions, tabs, agent resume (see above)
omarchy-session uninstall-hook
omarchy-session disable | enable    # turn autosave + auto-restore off/on
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
  "resume_agents": true
}
```

## Install / remove

```
omarchy plugin add ~/src/omarchy-session-restore --enable --yes
ln -sf ~/.config/omarchy/plugins/eric.session-restore/bin/omarchy-session ~/.local/bin/omarchy-session
# merge extensions/omarchy-menu-snippet.jsonc into ~/.config/omarchy/extensions/omarchy-menu.jsonc
omarchy menu refresh
```

Update after editing the repo: commit, then `omarchy plugin update eric.session-restore --yes`.

Turn off temporarily: `omarchy-session disable` (or `omarchy plugin disable eric.session-restore`).

Remove completely:

```
omarchy plugin remove eric.session-restore
rm ~/.local/bin/omarchy-session
# delete the four session rows from ~/.config/omarchy/extensions/omarchy-menu.jsonc, then:
omarchy menu refresh
rm -r ~/.local/state/omarchy/session-restore ~/.config/omarchy/session-restore.json
```

## Limitations

* Browsers only get their windows back if the browser itself restores them
  (Chrome: Settings → On startup → *Continue where you left off*, or crash
  recovery after a reboot). Chromium-family multi-profile setups launch each
  profile with `--profile-directory` so the profile picker does not appear.
  Windows are matched by title (and, for Chromium, attributed to a profile via
  the signed-in email in the title or titles stored in that profile's session
  files).
* Two tiled windows on the same workspace are re-ordered left-to-right after
  restore to match their saved positions; if Hyprland's layout still disagrees
  they may remain swapped — drag one past the other once.
* Terminal scrollback and running processes aren't preserved, only the
  folder, the Atuin session (with the hook), a known TUI program relaunched
  fresh, and coding agents resumed into their conversation.
* Tab-to-window assignment is a guess based on start times. Ghostty splits
  come back as tabs. Terminals that were open before the hook was installed
  get a new Atuin session the first time around. Restored ghostty windows
  run as separate processes (`--gtk-single-instance=false`) because a
  single-instance hand-off ignores `--working-directory`.
* Apps whose window title/state lives inside the app (editors, Electron apps)
  reopen however they normally do; documents aren't reopened unless they were
  on the original command line.
* Tiled layout order is approximated by launching left-to-right per workspace;
  exact split ratios aren't restored.
* A hard power-off without the menu still restores the last autosave (≤ 60 s old).
* Logging out via `uwsm stop` / a keybinding rather than the menu skips the
  final snapshot (the autosave is used instead).
