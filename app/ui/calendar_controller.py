import calendar
from datetime import datetime
import tkinter as tk

from app.ui.calendar_detail_window import CalendarDetailView


class CalendarController:
    def __init__(self, owner):
        self.owner = owner
        today = datetime.now().date()
        self.detail_year = today.year
        self.detail_month = today.month
        self.selected_date = today
        self.detail_view = None

        self.month_label = None
        self.hint_label = None
        self.grid = None
        self.dashboard_state = None

    def attach_dashboard_widgets(self, month_label, hint_label, grid):
        self.month_label = month_label
        self.hint_label = hint_label
        self.grid = grid

    def update_dashboard(self, study_dates, task_metrics):
        self.dashboard_state = {
            "study_dates": study_dates,
            "tasks_by_date": task_metrics["calendar_tasks_by_date"],
            "due_today": task_metrics["due_today"],
            "overdue_tasks": task_metrics["overdue_tasks"],
        }
        self.render_dashboard_calendar(
            study_dates=self.dashboard_state["study_dates"],
            tasks_by_date=self.dashboard_state["tasks_by_date"],
            due_today=self.dashboard_state["due_today"],
            overdue_tasks=self.dashboard_state["overdue_tasks"],
        )

    def refresh_dashboard_layout(self):
        if self.dashboard_state is None:
            return

        self.render_dashboard_calendar(
            study_dates=self.dashboard_state["study_dates"],
            tasks_by_date=self.dashboard_state["tasks_by_date"],
            due_today=self.dashboard_state["due_today"],
            overdue_tasks=self.dashboard_state["overdue_tasks"],
        )

    def render_dashboard_calendar(
        self,
        study_dates=None,
        due_dates=None,
        overdue_dates=None,
        tasks_by_date=None,
        due_today=0,
        overdue_tasks=0,
    ):
        if self.grid is None or self.month_label is None or self.hint_label is None:
            return

        for child in self.grid.winfo_children():
            child.destroy()

        today_datetime = datetime.now()
        today = today_datetime.date()
        study_dates = study_dates or set()
        tasks_by_date = tasks_by_date or {}
        today_tasks = list(tasks_by_date.get(today, []))
        today_tasks.sort(key=lambda item: (item["due_at"], item["task_id"]))

        self.month_label.config(
            text=f"{today_datetime.strftime('%A, %B')} {today.day}, {today.year}"
        )
        self.hint_label.config(
            text=self._build_dashboard_hint(
                today,
                study_dates,
                today_tasks,
                due_today,
                overdue_tasks,
            )
        )
        self.grid.configure(bg=self.owner.colors["card_alt"])
        self._render_today_timeline(today, today_tasks)

    def build_task_index(self, tasks, year, month):
        tasks_by_date = {}
        month_tasks = []

        for task in tasks:
            due_at = self.owner._parse_due_datetime(task)
            if due_at is None or due_at.year != year or due_at.month != month:
                continue

            task_entry = {
                "task_id": str(task.get("task_id", "")),
                "title": task.get("title", "Untitled Task"),
                "due_at": due_at,
                "status": task.get("status", "pending"),
                "notes": task.get("notes", ""),
            }
            tasks_by_date.setdefault(due_at.date(), []).append(task_entry)
            month_tasks.append(task_entry)

        for day_tasks in tasks_by_date.values():
            day_tasks.sort(key=lambda item: (item["due_at"], item["task_id"]))

        month_tasks.sort(key=lambda item: (item["due_at"], item["task_id"]))
        return tasks_by_date, month_tasks

    def open_detail(self, selected_date=None):
        if selected_date is not None:
            self.selected_date = selected_date
            self.detail_year = selected_date.year
            self.detail_month = selected_date.month

        callbacks = {
            "back": self.close_detail,
            "prev_month": lambda: self.shift_month(-1),
            "next_month": lambda: self.shift_month(1),
            "today": self.show_today,
            "select_date": self.select_date,
            "open_task": lambda task_id: self.owner.open_activity_detail(task_id),
        }

        if self.detail_view is None:
            self.detail_view = CalendarDetailView(
                self.owner.detail_container,
                self.owner.colors,
                callbacks,
            )
            self.owner._register_virtual_button_targets(self.detail_view)
            self.owner.calendar_detail_view = self.detail_view

        self.owner._show_detail_view(self.detail_view)
        self.sync_detail()

    def close_detail(self):
        if self.detail_view is not None:
            self.detail_view.pack_forget()
        self.owner.detail_container.pack_forget()
        self.owner.main_container.pack(fill="both", expand=True, padx=24, pady=24)
        self.owner._refresh_dashboard_metrics(force=True)

    def select_date(self, selected_date):
        self.selected_date = selected_date
        self.detail_year = selected_date.year
        self.detail_month = selected_date.month
        self.sync_detail()

    def shift_month(self, delta):
        month_index = (self.detail_year * 12) + (self.detail_month - 1) + delta
        new_year = month_index // 12
        new_month = (month_index % 12) + 1
        max_day = calendar.monthrange(new_year, new_month)[1]
        selected_day = min(self.selected_date.day, max_day)
        self.detail_year = new_year
        self.detail_month = new_month
        self.selected_date = datetime(new_year, new_month, selected_day).date()
        self.sync_detail()

    def show_today(self):
        today = datetime.now().date()
        self.detail_year = today.year
        self.detail_month = today.month
        self.selected_date = today
        self.sync_detail()

    def sync_detail(self):
        if self.detail_view is None:
            return

        max_day = calendar.monthrange(self.detail_year, self.detail_month)[1]
        if (
            self.selected_date.year != self.detail_year
            or self.selected_date.month != self.detail_month
        ):
            self.selected_date = datetime(self.detail_year, self.detail_month, 1).date()
        elif self.selected_date.day > max_day:
            self.selected_date = datetime(self.detail_year, self.detail_month, max_day).date()

        tasks = self.owner.task_manager.read_tasks()
        tasks_by_date, month_tasks = self.build_task_index(
            tasks,
            self.detail_year,
            self.detail_month,
        )
        self.detail_view.update_state(
            display_year=self.detail_year,
            display_month=self.detail_month,
            selected_date=self.selected_date,
            tasks_by_date=tasks_by_date,
            month_tasks=month_tasks,
        )

    def _build_dashboard_hint(
        self,
        today,
        study_dates,
        today_tasks,
        due_today,
        overdue_tasks,
    ):
        study_text = "Study session logged today." if today in study_dates else "No study session logged today."
        task_count = len(today_tasks)
        task_text = (
            f"{task_count} task{'s' if task_count != 1 else ''} scheduled today."
            if task_count
            else "No activity tasks scheduled today."
        )

        if overdue_tasks > 0:
            return f"{study_text} {task_text} {overdue_tasks} overdue."
        if due_today > 0:
            return f"{study_text} {task_text}"
        return f"{study_text} {task_text}"

    def _render_today_timeline(self, today, today_tasks):
        self.grid.update_idletasks()
        available_width = max(self.grid.winfo_width(), 260)
        available_height = max(self.grid.winfo_height(), 250)

        outer = tk.Frame(self.grid, bg=self.owner.colors["card_alt"])
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg=self.owner.colors["card_alt"])
        header.pack(fill="x", pady=(0, 10))

        tk.Label(
            header,
            text="Today's Schedule",
            font=("Arial", 12, "bold"),
            bg=self.owner.colors["card_alt"],
            fg=self.owner.colors["accent_bright"],
            anchor="w",
        ).pack(side="left")

        tk.Label(
            header,
            text=today.strftime("%d %b"),
            font=("Arial", 10),
            bg=self.owner.colors["card_alt"],
            fg=self.owner.colors["muted"],
            anchor="e",
        ).pack(side="right")

        timeline_height = max(220, min(available_height - 18, 360))
        timeline_frame = tk.Frame(outer, bg=self.owner.colors["card_alt"], height=timeline_height)
        timeline_frame.pack(fill="both", expand=True)
        timeline_frame.pack_propagate(False)

        hours_frame = tk.Frame(
            timeline_frame,
            bg=self.owner.colors["card_alt"],
            width=60,
            height=timeline_height,
        )
        hours_frame.pack(side="left", fill="y", padx=(0, 10))
        hours_frame.pack_propagate(False)

        lane_frame = tk.Frame(
            timeline_frame,
            bg="#091017",
            highlightbackground=self.owner.colors["border"],
            highlightthickness=1,
            height=timeline_height,
        )
        lane_frame.pack(side="left", fill="both", expand=True)
        lane_frame.pack_propagate(False)

        start_hour = 6
        end_hour = 22
        hour_span = end_hour - start_hour
        block_height = 48 if timeline_height >= 280 else 40

        for hour in range(start_hour, end_hour + 1, 2):
            y_position = self._timeline_position(hour, start_hour, hour_span, timeline_height)
            hour_label = tk.Label(
                hours_frame,
                text=self._format_hour_label(hour),
                font=("Arial", 9),
                bg=self.owner.colors["card_alt"],
                fg=self.owner.colors["muted"],
                anchor="e",
                justify="right",
            )
            hour_label.place(x=0, y=max(0, y_position - 9), width=56, height=18)

            guide = tk.Frame(lane_frame, bg="#22303B", height=1)
            guide.place(x=0, y=y_position, relwidth=1.0)

        if not today_tasks:
            self._set_calendar_date_action(lane_frame, today)
            self._set_calendar_date_action(hours_frame, today)
            return

        previous_bottom = 8
        for task in today_tasks:
            hour_value = task["due_at"].hour + (task["due_at"].minute / 60)
            y_center = self._timeline_position(hour_value, start_hour, hour_span, timeline_height)
            top = max(8, min(timeline_height - block_height - 8, y_center - (block_height // 2)))
            top = max(top, previous_bottom)
            previous_bottom = min(timeline_height - 8, top + block_height + 8)

            block = tk.Frame(
                lane_frame,
                bg=self._task_block_color(task),
                highlightbackground=self._task_block_border(task),
                highlightthickness=1,
                padx=10,
                pady=6,
            )
            block.place(x=12, y=top, relwidth=0.9, height=block_height)

            time_label = tk.Label(
                block,
                text=task["due_at"].strftime("%H:%M"),
                font=("Arial", 10, "bold"),
                bg=block.cget("bg"),
                fg=self._task_block_text_color(task),
                anchor="w",
            )
            time_label.pack(anchor="w")

            title_label = tk.Label(
                block,
                text=self._truncate_text(task["title"], 34),
                font=("Arial", 10),
                bg=block.cget("bg"),
                fg=self._task_block_text_color(task),
                anchor="w",
                justify="left",
                wraplength=max(160, available_width - 170),
            )
            title_label.pack(anchor="w", pady=(2, 0))

            self._set_task_action(block, task["task_id"])
            self._set_task_action(time_label, task["task_id"])
            self._set_task_action(title_label, task["task_id"])

        self._set_calendar_date_action(lane_frame, today)
        self._set_calendar_date_action(hours_frame, today)

    def _timeline_position(self, hour_value, start_hour, hour_span, timeline_height):
        clamped = min(max(hour_value, start_hour), start_hour + hour_span)
        usable_height = max(1, timeline_height - 16)
        ratio = (clamped - start_hour) / hour_span if hour_span else 0
        return 8 + int(ratio * usable_height)

    def _format_hour_label(self, hour):
        if hour == 0:
            return "12 AM"
        if hour < 12:
            return f"{hour} AM"
        if hour == 12:
            return "12 PM"
        return f"{hour - 12} PM"

    def _task_block_color(self, task):
        if task.get("status") == "completed":
            return "#16202A"
        return "#173239"

    def _task_block_border(self, task):
        if task.get("status") == "completed":
            return "#30526A"
        return self.owner.colors["teal"]

    def _task_block_text_color(self, task):
        if task.get("status") == "completed":
            return self.owner.colors["muted"]
        return self.owner.colors["text"]

    def _truncate_text(self, text, limit):
        compact_text = " ".join(text.split())
        if len(compact_text) <= limit:
            return compact_text
        return f"{compact_text[:limit - 3]}..."

    def _set_task_action(self, widget, task_id):
        self.owner._set_hitbox_action(
            widget,
            lambda chosen_task_id=task_id: self.owner.open_activity_detail(chosen_task_id),
            f"open_activity_detail:{task_id}",
        )
        try:
            widget.configure(cursor="hand2")
        except Exception:
            pass

    def _set_calendar_date_action(self, widget, selected_date):
        self.owner._set_hitbox_action(
            widget,
            lambda chosen_date=selected_date: self.open_detail(chosen_date),
            f"open_calendar_detail:{selected_date.isoformat()}",
        )
        try:
            widget.configure(cursor="hand2")
        except Exception:
            pass
