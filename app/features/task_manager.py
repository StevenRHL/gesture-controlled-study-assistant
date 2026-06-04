import csv
from datetime import datetime
from pathlib import Path


class TaskManager:
    def __init__(self, file_path="data/activity_tasks.csv"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        self.headers = [
            "task_id",
            "title",
            "due_date",
            "due_time",
            "notes",
            "status",
            "created_at",
            "completed_at",
        ]

        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not self.file_path.exists():
            with open(self.file_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=self.headers)
                writer.writeheader()

    def read_tasks(self):
        self._ensure_file_exists()

        with open(self.file_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            tasks = list(reader)

        return sorted(tasks, key=self._sort_key)

    def add_task(self, title, due_date, due_time, notes):
        task = {
            "task_id": self._get_next_task_id(),
            "title": title,
            "due_date": due_date,
            "due_time": due_time,
            "notes": notes,
            "status": "pending",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "completed_at": "",
        }

        with open(self.file_path, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.headers)
            writer.writerow(task)

        return task

    def update_task_status(self, task_id, status):
        tasks = self.read_tasks()
        updated = False

        for task in tasks:
            if task["task_id"] != str(task_id):
                continue

            task["status"] = status
            task["completed_at"] = (
                datetime.now().isoformat(timespec="seconds")
                if status == "completed"
                else ""
            )
            updated = True
            break

        if updated:
            self._write_tasks(tasks)

        return updated

    def delete_task(self, task_id):
        tasks = self.read_tasks()
        filtered_tasks = [
            task for task in tasks
            if task["task_id"] != str(task_id)
        ]

        deleted = len(filtered_tasks) != len(tasks)
        if deleted:
            self._write_tasks(filtered_tasks)

        return deleted

    def _get_next_task_id(self):
        tasks = self.read_tasks()
        if not tasks:
            return 1

        return max(int(task["task_id"]) for task in tasks) + 1

    def _write_tasks(self, tasks):
        with open(self.file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.headers)
            writer.writeheader()
            writer.writerows(tasks)

    def _sort_key(self, task):
        status_rank = 0 if task.get("status") != "completed" else 1

        try:
            due_at = datetime.strptime(
                f"{task.get('due_date', '')} {task.get('due_time', '')}",
                "%Y-%m-%d %H:%M",
            )
        except ValueError:
            due_at = datetime.max

        try:
            task_id = int(task.get("task_id", 0))
        except ValueError:
            task_id = 0

        return (status_rank, due_at, task_id)
