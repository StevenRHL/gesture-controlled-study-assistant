import tkinter as tk
from tkinter import ttk


class SessionsWindow:
    def __init__(self, parent, session_logger):
        self.parent = parent
        self.session_logger = session_logger

        self.window = tk.Toplevel(parent)
        self.window.title("Study Sessions")
        self.window.geometry("850x400")
        self.window.configure(bg="#f5f5f5")

        self._build_ui()
        self.load_sessions()

    def _build_ui(self):
        title_label = tk.Label(
            self.window,
            text="Study Sessions",
            font=("Arial", 20, "bold"),
            bg="#000000"
        )
        title_label.pack(pady=15)

        table_frame = tk.Frame(self.window, bg="#ff0000")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = (
            "session_id",
            "task_name",
            "date",
            "start_time",
            "end_time",
            "duration_minutes",
            "status",
            "pauses"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=10
        )

        self.tree.heading("session_id", text="ID")
        self.tree.heading("task_name", text="Task")
        self.tree.heading("date", text="Date")
        self.tree.heading("start_time", text="Start")
        self.tree.heading("end_time", text="End")
        self.tree.heading("duration_minutes", text="Minutes")
        self.tree.heading("status", text="Status")
        self.tree.heading("pauses", text="Pauses")

        self.tree.column("session_id", width=50, anchor="center")
        self.tree.column("task_name", width=220)
        self.tree.column("date", width=100, anchor="center")
        self.tree.column("start_time", width=90, anchor="center")
        self.tree.column("end_time", width=90, anchor="center")
        self.tree.column("duration_minutes", width=80, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("pauses", width=70, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        button_frame = tk.Frame(self.window, bg="#f5f5f5")
        button_frame.pack(pady=10)

        refresh_button = tk.Button(
            button_frame,
            text="Refresh",
            width=12,
            command=self.load_sessions
        )
        refresh_button.pack(side="left", padx=5)

        close_button = tk.Button(
            button_frame,
            text="Close",
            width=12,
            command=self.window.destroy
        )
        close_button.pack(side="left", padx=5)

    def load_sessions(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        sessions = self.session_logger.read_sessions()

        for session in sessions:
            self.tree.insert(
                "",
                "end",
                values=(
                    session["session_id"],
                    session["task_name"],
                    session["date"],
                    session["start_time"],
                    session["end_time"],
                    session["duration_minutes"],
                    session["status"],
                    session["pauses"]
                )
            )