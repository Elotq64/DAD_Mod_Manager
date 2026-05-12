import requests
import time
from PySide6.QtCore import QThread, Signal
from .constants import VERSION, API_URL, USER_AGENT

class UpdateChecker(QThread):
    # Signals: found_update(latest_version, url, changelog), error(msg), up_to_date()
    found_update = Signal(str, str, str)
    error = Signal(str)
    up_to_date = Signal()

    def __init__(self, manual=False):
        super().__init__()
        self.manual = manual

    def run(self):
        try:
            headers = {'User-Agent': USER_AGENT}
            response = requests.get(API_URL, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()

            latest_version = data.get("tag_name", "").lstrip('v')
            html_url = data.get("html_url", "")
            changelog = data.get("body", "")

            if self.is_newer(latest_version, VERSION):
                self.found_update.emit(latest_version, html_url, changelog)
            else:
                self.up_to_date.emit()
        except Exception as e:
            if self.manual:
                self.error.emit(str(e))
            else:
                # Silent fail for background check
                print(f"Update check failed: {e}")

    @staticmethod
    def is_newer(remote, local):
        import re
        def parse(v):
            # Extract only numbers and dots (e.g. "stable6.0" -> [6, 0])
            match = re.search(r'(\d+(?:\.\d+)*)', v)
            if match:
                return [int(x) for x in match.group(1).split('.')]
            return []

        rv = parse(remote)
        lv = parse(local)
        
        # Pad with zeros
        max_len = max(len(rv), len(lv))
        rv += [0] * (max_len - len(rv))
        lv += [0] * (max_len - len(lv))
        
        for r, l in zip(rv, lv):
            if r > l: return True
            if r < l: return False
        return False
