#!/usr/bin/python3

import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QSharedMemory, QTimer, QUrl, Qt
from PyQt6.QtGui import QAction, QColor, QDesktopServices
from PyQt6.QtGui import QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

VPN_HOST = "myupclink.upc.edu:443"
SAML_URL = "https://myupclink.upc.edu:443/remote/saml/start?redirect=1"


def vpn_process_running():
    return subprocess.run(
        ["/usr/bin/pgrep", "-x", "openfortivpn"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def vpn_interface_present():
    try:
        return any(Path("/sys/class/net").glob("ppp*"))
    except OSError:
        return False


def create_icon(colour):
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(colour))
    painter.setPen(QPen(QColor("white"), 3))
    painter.drawEllipse(5, 5, 54, 54)

    font = painter.font()
    font.setBold(True)
    font.setPixelSize(34)
    painter.setFont(font)
    painter.drawText(
        pixmap.rect(),
        Qt.AlignmentFlag.AlignCenter,
        "U",
    )
    painter.end()

    return QIcon(pixmap)


class UpclinkTray:
    def __init__(self, app):
        self.app = app
        self.state = "disconnected"

        self.icons = {
            "disconnected": create_icon("#7f8c8d"),
            "connecting": create_icon("#f1c40f"),
            "connected": create_icon("#2ecc71"),
        }

        self.tray = QSystemTrayIcon(self.icons["disconnected"], app)
        self.menu = QMenu()

        self.status_action = QAction("Estado: comprobando…")
        self.status_action.setEnabled(False)

        self.connect_action = QAction("Conectar")
        self.connect_action.triggered.connect(self.connect)

        self.sso_action = QAction("Abrir autenticación SSO")
        self.sso_action.triggered.connect(self.open_sso)

        self.disconnect_action = QAction("Desconectar")
        self.disconnect_action.triggered.connect(self.disconnect)

        self.quit_action = QAction("Cerrar indicador")
        self.quit_action.triggered.connect(app.quit)

        self.menu.addAction(self.status_action)
        self.menu.addSeparator()
        self.menu.addAction(self.connect_action)
        self.menu.addAction(self.sso_action)
        self.menu.addAction(self.disconnect_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.clicked)
        self.tray.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)

        self.refresh()

    def get_state(self):
        if vpn_process_running() and vpn_interface_present():
            return "connected"

        if vpn_process_running():
            return "connecting"

        return "disconnected"

    def refresh(self):
        self.state = self.get_state()

        labels = {
            "disconnected": "Desconectada",
            "connecting": "Esperando autenticación SSO",
            "connected": "Conectada",
        }

        label = labels[self.state]

        self.tray.setIcon(self.icons[self.state])
        self.tray.setToolTip(f"UPClink VPN — {label}")
        self.status_action.setText(f"Estado: {label}")

        self.connect_action.setEnabled(self.state == "disconnected")
        self.sso_action.setEnabled(self.state == "connecting")
        self.disconnect_action.setEnabled(
            self.state != "disconnected"
        )

    def connect(self):
        if vpn_process_running():
            return

        subprocess.Popen(
            [
                "/usr/bin/konsole",
                "--hold",
                "-e",
                "/usr/bin/sudo",
                "/usr/bin/openfortivpn",
                VPN_HOST,
                "--saml-login",
            ],
            start_new_session=True,
        )

    def open_sso(self):
        QDesktopServices.openUrl(QUrl(SAML_URL))

    def disconnect(self):
        if not vpn_process_running():
            return

        subprocess.Popen(
            [
                "/usr/bin/pkexec",
                "/usr/bin/pkill",
                "-INT",
                "-x",
                "openfortivpn",
            ]
        )

    def clicked(self, reason):
        if reason != QSystemTrayIcon.ActivationReason.Trigger:
            return

        if self.state == "disconnected":
            self.connect()
        elif self.state == "connecting":
            self.open_sso()
        else:
            self.tray.showMessage(
                "UPClink VPN",
                "La VPN está conectada.",
                QSystemTrayIcon.MessageIcon.Information,
                2500,
            )


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    shared_memory = QSharedMemory(
        "upclink-vpn-tray-single-instance"
    )

    if not shared_memory.create(1):
        return 0

    tray = UpclinkTray(app)

    app.upclink_tray = tray
    app.upclink_shared_memory = shared_memory

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
