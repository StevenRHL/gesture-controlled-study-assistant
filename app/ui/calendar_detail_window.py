import calendar
import tkinter as tk
from datetime import datetime


class CalendarDetailView(tk.Frame):
    def __init__(self, parent, colors, callbacks):
        super().__init__(parent, bg=colors["bg"])
        self.colors = colors
        self.callbacks = callbacks
        self.day_buttons = []
        self.selected_day_buttons = []
        self.month_task_buttons = []

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
            text="CALENDAR",
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

        nav_row = tk.Frame(container, bg=self.colors["card"])
        nav_row.pack(fill="x", pady=(0, 18))

        self._build_button(
            nav_row,
            "◀ Previous",
            self.callbacks["prev_month"],
            bg="#121B24",
        ).pack(side="left")

        self.month_label = tk.Label(
            nav_row,
            text="June 2026",
            font=("Arial", 22, "bold"),
            bg=self.colors["card"],
            fg=self.colors["accent_bright"],
        )
        self.month_label.pack(side="left", padx=18)

        self._build_button(
            nav_row,
            "Today",
            self.callbacks["today"],
            bg=self.colors["accent"],
            fg="#17120D",
        ).pack(side="left")

        self._build_button(
            nav_row,
            "Next ▶",
            self.callbacks["next_month"],
            bg="#121B24",
        ).pack(side="right")

        self.summary_label = tk.Label(
            container,
            text="Month summary appears here.",
            font=("Arial", 11),
            bg=self.colors["card"],
            fg=self.colors["muted"],
            anchor="w",
            justify="left",
        )
        self.summary_label.pack(fill="x", pady=(0, 18))

        weekdays_row = tk.Frame(container, bg=self.colors["card"])
        weekdays_row.pack(fill="x")
        for index, label in enumerate(("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")):
            weekdays_row.grid_columnconfigure(index, weight=1, uniform="calendar-detail-week")
            tk.Label(
                weekdays_row,
                text=label,
                font=("Arial", 10, "bold"),
                bg=self.colors["card"],
                fg=self.colors["muted"],
                anchor="center",
            ).grid(row=0, column=index, sticky="ew", padx=4, pady=(0, 8))

        self.month_grid = tk.Frame(container, bg=self.colors["card"])
        self.month_grid.pack(fill="x", pady=(0, 18))
        for row_index in range(6):
            self.month_grid.grid_rowconfigure(row_index, weight=1, uniform="calendar-detail-row")
        for column_index in range(7):
            self.month_grid.grid_columnconfigure(column_index, weight=1, uniform="calendar-detail-column")

        for row_index in range(6):
            for column_index in range(7):
                button = self._build_day_button(self.month_grid)
                button.grid(
                    row=row_index,
                    column=column_index,
                    sticky="nsew",
                    padx=4,
                    pady=4,
                )
                self.day_buttons.append(button)

        detail_row = tk.Frame(container, bg=self.colors["card"])
        detail_row.pack(fill="both", expand=True)

        selected_day_panel = tk.Frame(
            detail_row,
            bg=self.colors["card_alt"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=18,
            pady=18,
        )
        selected_day_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(
            selected_day_panel,
            text="Selected Day",
            font=("Arial", 16, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["accent_bright"],
        ).pack(anchor="w")

        self.selected_day_label = tk.Label(
            selected_day_panel,
            text="Monday, June 9, 2026",
            font=("Arial", 13, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["text"],
        )
        self.selected_day_label.pack(anchor="w", pady=(8, 6))

        self.selected_day_summary_label = tk.Label(
            selected_day_panel,
            text="Tasks due on the selected day appear here.",
            font=("Arial", 11),
            bg=self.colors["card_alt"],
            fg=self.colors["muted"],
            justify="left",
            anchor="w",
            wraplength=360,
        )
        self.selected_day_summary_label.pack(fill="x", pady=(0, 12))

        for _ in range(6):
            button = self._build_task_button(selected_day_panel)
            button.pack(fill="x", pady=4)
            self.selected_day_buttons.append(button)

        month_tasks_panel = tk.Frame(
            detail_row,
            bg=self.colors["card_alt"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=18,
            pady=18,
        )
        month_tasks_panel.pack(side="left", fill="both", expand=True, padx=(10, 0))

        tk.Label(
            month_tasks_panel,
            text="This Month's Activity Tasks",
            font=("Arial", 16, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["accent_bright"],
        ).pack(anchor="w")

        self.month_tasks_summary_label = tk.Label(
            month_tasks_panel,
            text="Tasks due this month appear here.",
            font=("Arial", 11),
            bg=self.colors["card_alt"],
            fg=self.colors["muted"],
            justify="left",
            anchor="w",
            wraplength=360,
        )
        self.month_tasks_summary_label.pack(fill="x", pady=(8, 12))

        for _ in range(10):
            button = self._build_task_button(month_tasks_panel)
            button.pack(fill="x", pady=4)
            self.month_task_buttons.append(button)

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

    def _build_day_button(self, parent):
        return tk.Button(
            parent,
            text="",
            command=lambda: None,
            font=("Arial", 10, "bold"),
            relief="flat",
            bd=0,
            justify="left",
            anchor="nw",
            padx=10,
            pady=10,
            height=4,
            wraplength=150,
            bg="#0E141C",
            fg=self.colors["text"],
            activebackground="#0E141C",
            activeforeground=self.colors["text"],
            highlightbackground="#22303B",
            highlightthickness=1,
            cursor="hand2",
        )

    def _build_task_button(self, parent):
        return tk.Button(
            parent,
            text="",
            command=lambda: None,
            font=("Arial", 10),
            relief="flat",
            bd=0,
            justify="left",
            anchor="w",
            padx=12,
            pady=10,
            wraplength=360,
            bg="#101722",
            fg=self.colors["text"],
            activebackground="#16202C",
            activeforeground=self.colors["text"],
            highlightbackground="#22303B",
            highlightthickness=1,
            cursor="hand2",
        )

    def update_state(
        self,
        display_year,
        display_month,
        selected_date,
        tasks_by_date,
        month_tasks,
    ):
        month_name = calendar.month_name[display_month]
        self.month_label.config(text=f"{month_name} {display_year}")

        total_month_tasks = len(month_tasks)
        due_days = len(tasks_by_date)
        self.summary_label.config(
            text=(
                f"{total_month_tasks} task{'s' if total_month_tasks != 1 else ''} due in {month_name}. "
                f"{due_days} calendar day{'s' if due_days != 1 else ''} have scheduled activity."
            )
        )

        weeks = calendar.monthcalendar(display_year, display_month)
        while len(weeks) < 6:
            weeks.append([0] * 7)
        today = self._current_date()

        selected_tasks = tasks_by_date.get(selected_date, [])

        button_index = 0
        for week in weeks:
            for day in week:
                button = self.day_buttons[button_index]
                button_index += 1

                if day == 0:
                    button.config(
                        text="",
                        state="disabled",
                        bg="#0D1218",
                        fg=self.colors["subtle"],
                        activebackground="#0D1218",
                        activeforeground=self.colors["subtle"],
                        command=lambda: None,
                    )
                    continue

                cell_date = selected_date.replace(year=display_year, month=display_month, day=day)
                day_tasks = tasks_by_date.get(cell_date, [])
                button_text = self._format_day_button_text(day, day_tasks)
                bg, fg = self._day_button_colors(cell_date, selected_date, day_tasks, today)
                button.config(
                    text=button_text,
                    state="normal",
                    bg=bg,
                    fg=fg,
                    activebackground=bg,
                    activeforeground=fg,
                    command=lambda chosen_date=cell_date: self.callbacks["select_date"](chosen_date),
                )

        self.selected_day_label.config(text=selected_date.strftime("%A, %B %d, %Y"))
        if selected_tasks:
            self.selected_day_summary_label.config(
                text=(
                    f"{len(selected_tasks)} task{'s' if len(selected_tasks) != 1 else ''} due on this date."
                )
            )
        else:
            self.selected_day_summary_label.config(
                text="No activity tasks are due on this date."
            )

        self._update_task_buttons(
            self.selected_day_buttons,
            selected_tasks,
            empty_text="No tasks scheduled for the selected day.",
            formatter=self._format_selected_day_task,
        )
        self._update_task_buttons(
            self.month_task_buttons,
            month_tasks,
            empty_text="No activity tasks are due this month.",
            formatter=self._format_month_task,
        )

        if month_tasks:
            self.month_tasks_summary_label.config(
                text=(
                    f"{len(month_tasks)} task{'s' if len(month_tasks) != 1 else ''} due in this month."
                )
            )
        else:
            self.month_tasks_summary_label.config(
                text="No activity tasks are due this month."
            )

    def _format_day_button_text(self, day, day_tasks):
        if not day_tasks:
            return str(day)

        first_task = day_tasks[0]
        time_text = first_task["due_at"].strftime("%H:%M")
        title = self._truncate_text(first_task["title"], 16)
        if len(day_tasks) == 1:
            return f"{day}\n{title}\n{time_text}"
        return f"{day}\n{title}\n+{len(day_tasks) - 1} more"

    def _day_button_colors(self, cell_date, selected_date, day_tasks, today):
        if cell_date == selected_date:
            return self.colors["accent"], "#1A1208"

        if day_tasks:
            if any(task["status"] != "completed" and task["due_at"].date() < today for task in day_tasks):
                return "#2A1113", self.colors["danger"]
            if any(task["status"] != "completed" for task in day_tasks):
                return self.colors["teal_soft"], self.colors["teal"]
            return "#1A2230", self.colors["muted"]

        if cell_date == today:
            return self.colors["accent_soft"], self.colors["accent_bright"]

        return "#0E141C", self.colors["text"]

    def _update_task_buttons(self, buttons, tasks, empty_text, formatter):
        for index, button in enumerate(buttons):
            if not tasks and index == 0:
                button.config(
                    text=empty_text,
                    state="disabled",
                    command=lambda: None,
                    bg="#101722",
                    fg=self.colors["muted"],
                    activebackground="#101722",
                    activeforeground=self.colors["muted"],
                )
                continue

            if index >= len(tasks):
                button.config(
                    text="",
                    state="disabled",
                    command=lambda: None,
                    bg="#101722",
                    fg=self.colors["text"],
                    activebackground="#101722",
                    activeforeground=self.colors["text"],
                )
                continue

            task = tasks[index]
            button.config(
                text=formatter(task),
                state="normal",
                command=lambda task_id=task["task_id"]: self.callbacks["open_task"](task_id),
                bg="#101722" if task["status"] != "completed" else "#16202C",
                fg=self.colors["text"] if task["status"] != "completed" else self.colors["muted"],
                activebackground="#16202C",
                activeforeground=self.colors["text"] if task["status"] != "completed" else self.colors["muted"],
            )

    def _format_selected_day_task(self, task):
        due_at = task["due_at"].strftime("%H:%M")
        status_text = "Done" if task["status"] == "completed" else "Due"
        return f"{due_at}  |  {task['title']}\n{status_text}  |  {task['due_at'].strftime('%Y-%m-%d')}"

    def _format_month_task(self, task):
        due_text = task["due_at"].strftime("%a %Y-%m-%d %H:%M")
        status_text = "Done" if task["status"] == "completed" else "Pending"
        return f"{due_text}\n{task['title']}  |  {status_text}"

    def _truncate_text(self, text, limit):
        compact_text = " ".join(text.split())
        if len(compact_text) <= limit:
            return compact_text
        return f"{compact_text[:limit - 3]}..."

    def _current_date(self):
        return datetime.now().date()
