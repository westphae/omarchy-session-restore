# omarchy-session-restore shell hook (bash and zsh) — part of eric.session-restore.
#
# Source this from ~/.bashrc / ~/.zshrc AFTER `atuin init` (or let
# `omarchy-session install-hook` add the line). It does two small things:
#   1. records this shell's ATUIN_SESSION in $XDG_RUNTIME_DIR so the next
#      save can give the restored terminal the same Atuin session, and
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
  (umask 077; printf '%s\n' "${ATUIN_SESSION:-}" >| "$__osr_d/shell-$$") 2>/dev/null
fi
unset __osr_d
