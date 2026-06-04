import tkinter as tk
from tkinter import ttk


class StudyProgressDetailView(tk.Frame):
    def __init__(self, parent, colors, callbacks):
        super().__init__(parent, bg=colors["bg"])
        self.colors = colors
        self.callbacks = callbacks
        self.day_rows = []

        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(
            self,
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=28,
            pady=24,
        )
        container.pack(fill="both", expand=True, padx=24, pady=24)

        header = tk.Frame(container, bg=self.colors["card"])
        header.pack(fill="x", pady=(0, 18))

        self._build_button(
            header,
            "← Back To Dashboard",
            self.callbacks["back"],
            bg="#121B24",
        ).pack(side="left")

        tk.Label(
            header,
            text="STUDY PROGRESS",
            font=("Arial", 24, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"],
        ).pack(side="left", padx=(18, 0))

        tk.Label(
            header,
            text="Detail View",
            font=("Arial", 12, "bold"),
            bg=self.colors["accent_soft"],
            fg=self.colors["accent_bright"],
            padx=14,
            pady=8,
        ).pack(side="right")

        summary_row = tk.Frame(container, bg=self.colors["card"])
        summary_row.pack(fill="x", pady=(0, 18))

        self.weekly_time_value = self._build_stat_block(
            summary_row,
            "Weekly Time",
            "0h 00m",
            self.colors["teal"],
        )
        self.weekly_sessions_value = self._build_stat_block(
            summary_row,
            "Sessions",
            "0",
            self.colors["accent"],
        )
        self.focus_score_value = self._build_stat_block(
            summary_row,
            "Focus Score",
            "0",
            self.colors["success"],
        )
        self.current_streak_value = self._build_stat_block(
            summary_row,
            "Current Streak",
            "0 days",
            self.colors["accent_bright"],
        )

        content_row = tk.Frame(container, bg=self.colors["card"])
        content_row.pack(fill="both", expand=True)

        overview_card = tk.Frame(
            content_row,
            bg=self.colors["card_alt"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=18,
            pady=18,
        )
        overview_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(
            overview_card,
            text="Weekly Goal Overview",
            font=("Arial", 16, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["text"],
        ).pack(anchor="w", pady=(0, 12))

        overview_body = tk.Frame(overview_card, bg=self.colors["card_alt"])
        overview_body.pack(fill="x")

        self.goal_canvas = tk.Canvas(
            overview_body,
            width=240,
            height=240,
            bg=self.colors["card_alt"],
            highlightthickness=0,
        )
        self.goal_canvas.pack(side="left", padx=(0, 18))
        self.goal_canvas.create_oval(
            28,
            28,
            212,
            212,
            outline=self.colors["teal_soft"],
            width=16,
        )
        self.goal_arc = self.goal_canvas.create_arc(
            28,
            28,
            212,
            212,
            start=90,
            extent=0,
            style="arc",
            outline=self.colors["teal"],
            width=16,
        )

        overview_info = tk.Frame(overview_body, bg=self.colors["card_alt"])
        overview_info.pack(side="left", fill="both", expand=True)

        self.goal_target_label = tk.Label(
            overview_info,
            text="Goal Target: 25h 00m",
            font=("Arial", 16, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["text"],
        )
        self.goal_target_label.pack(anchor="w", pady=(8, 10))

        self.goal_message_label = tk.Label(
            overview_info,
            text="Keep going.",
            font=("Arial", 13),
            bg=self.colors["card_alt"],
            fg=self.colors["accent_bright"],
            wraplength=340,
            justify="left",
        )
        self.goal_message_label.pack(anchor="w", pady=(0, 12))

        self.streak_message_label = tk.Label(
            overview_info,
            text="No sessions logged yet.",
            font=("Arial", 12),
            bg=self.colors["card_alt"],
            fg=self.colors["teal"],
            wraplength=340,
            justify="left",
        )
        self.streak_message_label.pack(anchor="w", pady=(0, 8))

        self.best_streak_label = tk.Label(
            overview_info,
            text="Best streak: 0 days",
            font=("Arial", 11),
            bg=self.colors["card_alt"],
            fg=self.colors["muted"],
        )
        self.best_streak_label.pack(anchor="w", pady=(0, 18))

        self.goal_progress_track = tk.Canvas(
            overview_info,
            width=320,
            height=14,
            bg=self.colors["card_alt"],
            highlightthickness=0,
        )
        self.goal_progress_track.pack(anchor="w", pady=(0, 10))
        self.goal_progress_track.create_rectangle(
            0,
            2,
            320,
            12,
            fill="#1D252D",
            outline="",
        )
        self.goal_progress_fill = self.goal_progress_track.create_rectangle(
            0,
            2,
            0,
            12,
            fill=self.colors["teal"],
            outline="",
        )

        self.goal_detail_label = tk.Label(
            overview_info,
            text="0h 00m studied this week.",
            font=("Arial", 12),
            bg=self.colors["card_alt"],
            fg=self.colors["text"],
        )
        self.goal_detail_label.pack(anchor="w")

        breakdown_card = tk.Frame(
            content_row,
            bg=self.colors["card_alt"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=18,
            pady=18,
        )
        breakdown_card.pack(side="left", fill="both", expand=True, padx=(10, 0))

        tk.Label(
            breakdown_card,
            text="7-Day Breakdown",
            font=("Arial", 16, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["text"],
        ).pack(anchor="w", pady=(0, 12))

        self.breakdown_summary_label = tk.Label(
            breakdown_card,
            text="Daily study totals appear here.",
            font=("Arial", 11),
            bg=self.colors["card_alt"],
            fg=self.colors["muted"],
            wraplength=360,
            justify="left",
        )
        self.breakdown_summary_label.pack(anchor="w", pady=(0, 12))

        for _ in range(7):
            row = tk.Frame(breakdown_card, bg=self.colors["card_alt"])
            row.pack(fill="x", pady=4)

            day_label = tk.Label(
                row,
                text="Mon",
                width=6,
                anchor="w",
                font=("Arial", 11, "bold"),
                bg=self.colors["card_alt"],
                fg=self.colors["accent_bright"],
            )
            day_label.pack(side="left")

            minutes_label = tk.Label(
                row,
                text="0h 00m",
                width=10,
                anchor="w",
                font=("Arial", 11),
                bg=self.colors["card_alt"],
                fg=self.colors["text"],
            )
            minutes_label.pack(side="left", padx=(0, 12))

            sessions_label = tk.Label(
                row,
                text="0 sessions",
                anchor="w",
                font=("Arial", 11),
                bg=self.colors["card_alt"],
                fg=self.colors["muted"],
            )
            sessions_label.pack(side="left")

            self.day_rows.append((day_label, minutes_label, sessions_label))

        recent_card = tk.Frame(
            container,
            bg=self.colors["card_alt"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=18,
            pady=18,
        )
        recent_card.pack(fill="both", expand=True, pady=(18, 0))

        recent_header = tk.Frame(recent_card, bg=self.colors["card_alt"])
        recent_header.pack(fill="x", pady=(0, 12))

        tk.Label(
            recent_header,
            text="Recent Study Sessions",
            font=("Arial", 16, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["text"],
        ).pack(side="left")

        self.session_count_label = tk.Label(
            recent_header,
            text="0 sessions tracked",
            font=("Arial", 11),
            bg=self.colors["card_alt"],
            fg=self.colors["accent_bright"],
        )
        self.session_count_label.pack(side="right")

        table_frame = tk.Frame(recent_card, bg=self.colors["card_alt"])
        table_frame.pack(fill="both", expand=True)

        columns = ("date", "task_name", "duration_minutes", "status", "pauses")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=8,
        )

        self.tree.heading("date", text="Date")
        self.tree.heading("task_name", text="Task")
        self.tree.heading("duration_minutes", text="Minutes")
        self.tree.heading("status", text="Status")
        self.tree.heading("pauses", text="Pauses")

        self.tree.column("date", width=120, anchor="center")
        self.tree.column("task_name", width=320)
        self.tree.column("duration_minutes", width=90, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("pauses", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _build_button(self, parent, text, command, bg="#121B24", fg=None):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Arial", 12, "bold"),
            relief="flat",
            bd=0,
            padx=10,
            pady=10,
            bg=bg,
            fg=fg or self.colors["text"],
            activebackground=bg,
            activeforeground=fg or self.colors["text"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            cursor="hand2",
        )

    def _build_stat_block(self, parent, label, value, accent):
        block = tk.Frame(parent, bg=self.colors["card_alt"])
        block.pack(side="left", fill="x", expand=True, padx=4)

        tk.Label(
            block,
            text=label,
            font=("Arial", 11),
            bg=self.colors["card_alt"],
            fg=self.colors["muted"],
        ).pack(anchor="w")

        value_label = tk.Label(
            block,
            text=value,
            font=("Arial", 24, "bold"),
            bg=self.colors["card_alt"],
            fg=accent,
        )
        value_label.pack(anchor="w", pady=(4, 0))
        return value_label

    def update_state(self, metrics, format_minutes):
        weekly_minutes = metrics["weekly_minutes"]
        goal_minutes = metrics["goal_minutes"]
        goal_ratio = min(weekly_minutes / goal_minutes, 1.0) if goal_minutes else 0.0

        self.weekly_time_value.config(text=format_minutes(weekly_minutes))
        self.weekly_sessions_value.config(text=str(metrics["weekly_sessions"]))
        self.focus_score_value.config(text=str(metrics["focus_score"]))
        self.current_streak_value.config(
            text=f"{metrics['current_streak']} day{'s' if metrics['current_streak'] != 1 else ''}"
        )

        self.goal_target_label.config(
            text=f"Goal Target: {format_minutes(goal_minutes)}"
        )
        self.goal_message_label.config(text=metrics["goal_message"])
        self.streak_message_label.config(text=metrics["streak_message"])
        self.best_streak_label.config(
            text=f"Best streak: {metrics['best_streak']} days"
        )
        self.goal_detail_label.config(
            text=(
                f"{format_minutes(weekly_minutes)} studied this week "
                f"across {metrics['weekly_sessions']} session"
                f"{'s' if metrics['weekly_sessions'] != 1 else ''}."
            )
        )
        self.breakdown_summary_label.config(
            text=(
                f"{metrics['days_with_sessions']} active day"
                f"{'s' if metrics['days_with_sessions'] != 1 else ''} in the last 7 days."
            )
        )
        self.session_count_label.config(
            text=f"{metrics['total_sessions']} sessions tracked"
        )

        self.goal_canvas.itemconfig(self.goal_arc, extent=-goal_ratio * 360)
        self.goal_canvas.delete("goal_text")
        self.goal_canvas.create_text(
            120,
            112,
            text=f"{int(goal_ratio * 100)}%",
            tags="goal_text",
            fill=self.colors["accent_bright"],
            font=("Arial", 28, "bold"),
        )
        self.goal_canvas.create_text(
            120,
            142,
            text="WEEKLY GOAL",
            tags="goal_text",
            fill=self.colors["muted"],
            font=("Arial", 10),
        )
        self.goal_progress_track.coords(
            self.goal_progress_fill,
            0,
            2,
            int(320 * goal_ratio),
            12,
        )

        for index, row in enumerate(self.day_rows):
            day_label, minutes_label, sessions_label = row
            day_label.config(text=metrics["day_labels"][index])
            minutes_label.config(text=format_minutes(metrics["day_minutes"][index]))
            session_count = metrics["day_sessions"][index]
            sessions_label.config(
                text=f"{session_count} session{'s' if session_count != 1 else ''}"
            )

        for item in self.tree.get_children():
            self.tree.delete(item)

        for session in metrics["recent_sessions"]:
            self.tree.insert(
                "",
                "end",
                values=(
                    session["date"],
                    session["task_name"],
                    session["duration_minutes"],
                    session["status"].title(),
                    session["pauses"],
                ),
            )
