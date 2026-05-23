import json

import requests
from PySide6.QtCore import QThread, Signal

from modules.config import api_url


class RealtimeEventsThread(QThread):
    event_received = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            try:
                with requests.get(api_url("/events/erp"), stream=True, timeout=(5, 60)) as response:
                    response.raise_for_status()
                    event_name = None
                    for raw_line in response.iter_lines(decode_unicode=True):
                        if not self._running:
                            break
                        if not raw_line:
                            event_name = None
                            continue

                        line = raw_line.strip()
                        if line.startswith("event:"):
                            event_name = line.split(":", 1)[1].strip()
                            continue

                        if event_name == "erp" and line.startswith("data:"):
                            payload = line.split(":", 1)[1].strip()
                            try:
                                self.event_received.emit(json.loads(payload))
                            except json.JSONDecodeError:
                                pass
            except Exception:
                if self._running:
                    self.msleep(3000)
