"""Optional transparent, always-on-top Qt host for the local avatar surface.

Start the BFI server first, then: uv run --group desktop python -m bfi.desktop
Native transparency/click-through needs verification on the owner's Windows PC.
"""

import argparse
import json
import sys
from urllib.parse import urlsplit

from bfi.config import ROOT


def local_url(value):
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise argparse.ArgumentTypeError(
            "Use the local BFI server origin, e.g. http://127.0.0.1:8000"
        )
    try:
        _ = parsed.port
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Invalid local port.") from exc
    return value.rstrip("/")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", type=local_url, default="http://127.0.0.1:8000")
    parser.add_argument("--click-through", action="store_true")
    args = parser.parse_args()
    try:
        from PySide6.QtCore import QPoint, Qt, QTimer, QUrl
        from PySide6.QtGui import QIcon
        from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
        from PySide6.QtWebEngineCore import QWebEnginePage
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtWidgets import (
            QApplication,
            QLabel,
            QMenu,
            QSystemTrayIcon,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:
        print("Desktop extras are missing. Run: uv sync --group desktop", file=sys.stderr)
        return 2

    app = QApplication([sys.argv[0]])
    app.setQuitOnLastWindowClosed(False)

    class DragHandle(QLabel):
        def mousePressEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.offset = event.globalPosition().toPoint() - window.pos()

        def mouseMoveEvent(self, event):
            if event.buttons() & Qt.MouseButton.LeftButton and hasattr(self, "offset"):
                window.move(event.globalPosition().toPoint() - self.offset)

        def contextMenuEvent(self, event):
            menu.exec(event.globalPos())

    class LocalPage(QWebEnginePage):
        def acceptNavigationRequest(self, url, kind, is_main):
            if not is_main:
                return True
            return url.toString().split("/overlay")[0] == args.url and url.path() == "/overlay"

    window = QWidget()
    window.setWindowTitle("BFI avatar")
    window.setWindowFlags(
        Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
    )
    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    layout = QVBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    handle = DragHandle("Drag · right-click for avatar controls")
    handle.setStyleSheet(
        "color:#58402b;background:rgba(245,240,229,190);font:10px sans-serif;padding:3px;"
    )
    layout.addWidget(handle)
    view = QWebEngineView()
    page = LocalPage(view)
    from PySide6.QtGui import QColor

    page.setBackgroundColor(QColor(0, 0, 0, 0))
    view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    view.setPage(page)
    view.setStyleSheet("background:transparent;")
    view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
    layout.addWidget(view)
    view.load(QUrl(args.url + "/overlay"))
    network = QNetworkAccessManager(window)
    flags = {"inflight": False, "layout": None}

    def request_state():
        if flags["inflight"]:
            return
        flags["inflight"] = True
        request = QNetworkRequest(QUrl(args.url + "/api/avatar"))
        request.setTransferTimeout(1500)
        reply = network.get(request)

        def received():
            flags["inflight"] = False
            try:
                state = json.loads(bytes(reply.readAll()))
                key = (state["dock"], state["size"])
                if flags["layout"] != key:
                    flags["layout"] = key
                    width, height = {
                        "small": (240, 400),
                        "normal": (320, 500),
                        "large": (400, 600),
                    }[key[1]]
                    area = window.screen().availableGeometry()
                    width = min(width, area.width())
                    height = min(height, area.height())
                    window.resize(width, height)
                    x = area.left() + 12 if key[0].endswith("left") else area.right() - width - 12
                    y = area.top() + 12 if key[0].startswith("top") else area.bottom() - height - 12
                    window.move(QPoint(x, y))
            except (ValueError, KeyError, TypeError):
                handle.setText("Start the local BFI handler · right-click for controls")
            finally:
                reply.deleteLater()

        reply.finished.connect(received)

    menu = QMenu()
    tray = QSystemTrayIcon(QIcon(str(ROOT / "bfi/static/mark.svg")), app)
    tray.setToolTip("BFI avatar — local presentation only")

    def show_avatar():
        window.show()
        request = QNetworkRequest(QUrl(args.url + "/api/avatar"))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        reply = network.post(request, b'{"visible":true}')
        reply.finished.connect(reply.deleteLater)

    menu.addAction("Show avatar", show_avatar)
    menu.addAction("Hide window", window.hide)
    through = menu.addAction("Click through avatar window")
    through.setCheckable(True)
    through.setEnabled(QSystemTrayIcon.isSystemTrayAvailable())

    def passthrough(enabled):
        window.setWindowFlag(Qt.WindowType.WindowTransparentForInput, enabled)
        window.show()

    through.toggled.connect(passthrough)
    menu.addAction("Quit avatar", app.quit)
    tray.setContextMenu(menu)
    tray.show()
    timer = QTimer(window)
    timer.timeout.connect(request_state)
    timer.start(750)
    window.resize(320, 500)
    window.show()
    request_state()
    if args.click_through and through.isEnabled():
        through.setChecked(True)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
