// eric.session-restore — headless service.
// Runs `bin/omarchy-session daemon`, which restores the previous session once
// right after login and then autosaves (timer + Hyprland window events).
// All logic lives in the Python CLI so it can be run and tested by hand.
import QtQuick
import Quickshell
import Quickshell.Io

Item {
  id: root

  readonly property string pluginDir: decodeURIComponent(Qt.resolvedUrl(".").toString().replace(/^file:\/\//, ""))
  property bool alive: true

  Process {
    id: daemon
    command: ["python3", root.pluginDir + "bin/omarchy-session", "daemon"]
    running: true
    onExited: (exitCode, exitStatus) => {
      // 75 = another daemon already holds the lock; check back later.
      if (root.alive) {
        restartTimer.interval = exitCode === 75 ? 60000 : 30000
        restartTimer.restart()
      }
    }
  }

  Timer {
    id: restartTimer
    repeat: false
    onTriggered: if (root.alive) daemon.running = true
  }

  Component.onDestruction: {
    root.alive = false
    daemon.running = false
  }
}
