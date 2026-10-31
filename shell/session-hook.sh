# omarchy-session-restore shell hook (bash and zsh) — part of eric.session-restore.
#
# Optional. Working directories are read from /proc and do not need this
# file. Source it from ~/.bashrc / ~/.zshrc AFTER `atuin init` only if you
# want the same Atuin session (and, on restore, the saved program started
# inside the new shell). `omarchy-session install-hook` adds that line;
# nothing in the normal install does.
#   1. records this shell's ATUIN_SESSION and $PWD in $XDG_RUNTIME_DIR so a
#      save can reuse the Atuin session, and can fall back to this directory
#      when /proc/<pid>/cwd cannot be read, and
#   2. when a restore opened this terminal (OMARCHY_SR_QUEUE is set), asks
#      omarchy-session for this tab's saved state — cwd, Atuin session and the
#      program to resume — and re-runs that program at the first prompt, so
#      the shell (with its history and integrations) stays open afterwards.
# Every value printed by `omarchy-session claim-tab` is shell-quoted.

[ -n "${BASH_VERSION:-}${ZSH_VERSION:-}" ] || return 0
case $- in *i*) ;; *) return 0 ;; esac

__osr_run() {
  local __f
  local -a __keep __r
  __keep=()
  for __f in "${precmd_functions[@]}"; do
    [ "$__f" = __osr_run ] || __keep+=("$__f")
  done
  precmd_functions=("${__keep[@]}")
  unset -f __osr_run
  __r=("${__osr_resume[@]}")
  unset __osr_resume
  [ ${#__r[@]} -gt 0 ] && "${__r[@]}"
}

__osr_arm() {
  unset -f __osr_arm
  if [ -n "${ZSH_VERSION:-}" ] || [ -n "${bash_preexec_imported:-}${__bp_imported:-}" ]; then
    precmd_functions+=(__osr_run)   # run at the first prompt
  else
    __osr_run                       # no precmd hooks available: run now
  fi
}

if [ -n "${OMARCHY_SR_QUEUE:-}" ]; then
  __osr_q=$OMARCHY_SR_QUEUE
  unset OMARCHY_SR_QUEUE
  __osr_code=$("${OMARCHY_SR_BIN:-$HOME/.local/bin/omarchy-session}" claim-tab "$__osr_q" 2>/dev/null)
  [ -n "$__osr_code" ] && eval "$__osr_code"
  unset __osr_q __osr_code
fi
unset OMARCHY_SR_BIN
type __osr_arm >/dev/null 2>&1 && unset -f __osr_arm

__osr_d="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/omarchy-session-restore"
if [ -d "$__osr_d" ] || mkdir -m 700 -p "$__osr_d" 2>/dev/null; then
  (umask 077; printf '%s\n%s\n' "${ATUIN_SESSION:-}" "${PWD:-}" >| "$__osr_d/shell-$$") 2>/dev/null
fi
unset __osr_d
