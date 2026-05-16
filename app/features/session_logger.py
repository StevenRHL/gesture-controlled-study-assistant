import csv
from pathlib import Path
from datetime import datetime


class SessionLogger:
    def __init__(self, file_path="data/study_sessions.csv"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        self.headers = [
            "session_id",
            "task_name",
            "date",
            "start_time",
            "end_time",
            "duration_minutes",
            "status",
            "pauses"
        ]

        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not self.file_path.exists():
            with open(self.file_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=self.headers)
                writer.writeheader()

    def _get_next_session_id(self):
        sessions = self.read_sessions()

        if not sessions:
            return 1

        last_id = max(int(session["session_id"]) for session in sessions)
        return last_id + 1

    def save_session(
        self,
        task_name,
        start_time,
        end_time,
        duration_minutes,
        status,
        pauses
    ):
        session = {
            "session_id": self._get_next_session_id(),
            "task_name": task_name,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "start_time": start_time,
            "end_time": end_time,
            "duration_minutes": duration_minutes,
            "status": status,
            "pauses": pauses
        }

        with open(self.file_path, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.headers)
            writer.writerow(session)

    def read_sessions(self):
        self._ensure_file_exists()

        with open(self.file_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return list(reader)