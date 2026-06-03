import tkinter as tk


class PomodoroDetailView(tk.Frame):
    def __init__(self, parent, colors, callbacks):
        super().__init__(parent, bg=colors["bg"])
        self.colors = colors
        self.callbacks = callbacks
        self.duration_var = tk.StringVar(value="25")

        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(
            self,
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=28,
            pady=24
        )
        container.pack(fill="both", expand=True, padx=24, pady=24)

        header = tk.Frame(container, bg=self.colors["card"])
        header.pack(fill="x", pady=(0, 18))

        self._build_button(
            header,
            "← Back To Dashboard",
            self.callbacks["back"],
            bg="#121B24"
        ).pack(side="left")

        tk.Label(
            header,
            text="POMODORO TIMER",
            font=("Arial", 24, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(side="left", padx=(18, 0))

        tk.Label(
            header,
            text="Detail View",
            font=("Arial", 12, "bold"),
            bg=self.colors["accent_soft"],
            fg=self.colors["accent_bright"],
            padx=14,
            pady=8
        ).pack(side="right")

        self.task_label = tk.Label(
            container,
            text="Task: Study Session",
            font=("Arial", 14),
            bg=self.colors["card"],
            fg=self.colors["muted"]
        )
        self.task_label.pack(anchor="w", pady=(0, 16))

        self.timer_canvas = tk.Canvas(
            container,
            width=500,
            height=500,
            bg=self.colors["card"],
            highlightthickness=0
        )
        self.timer_canvas.pack(pady=(0, 18))

        self.timer_canvas.create_oval(
            52,
            52,
            448,
            448,
            outline="#2A2118",
            width=22
        )
        self.timer_arc = self.timer_canvas.create_arc(
            52,
            52,
            448,
            448,
            start=90,
            extent=0,
            style="arc",
            outline=self.colors["accent"],
            width=22
        )

        timer_info = tk.Frame(self.timer_canvas, bg=self.colors["card"])
        self.timer_canvas.create_window(250, 250, window=timer_info)

        tk.Label(
            timer_info,
            text="FOCUS SESSION",
            font=("Arial", 16),
            bg=self.colors["card"],
            fg=self.colors["muted"]
        ).pack(pady=(0, 10))

        self.timer_label = tk.Label(
            timer_info,
            text="25:00",
            font=("Arial", 76, "bold"),
            bg=self.colors["card"],
            fg=self.colors["accent_bright"]
        )
        self.timer_label.pack()

        self.status_label = tk.Label(
            timer_info,
            text="Ready",
            font=("Arial", 20),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        self.status_label.pack(pady=(10, 6))

        self.hint_label = tk.Label(
            timer_info,
            text="Ready to begin.",
            font=("Arial", 13),
            bg=self.colors["card"],
            fg=self.colors["teal"]
        )
        self.hint_label.pack()

        controls = tk.Frame(container, bg=self.colors["card"])
        controls.pack(fill="x")

        duration_row = tk.Frame(controls, bg=self.colors["card"])
        duration_row.pack(fill="x", pady=(0, 12))
        for column in range(4):
            duration_row.grid_columnconfigure(column, weight=1, uniform="detail-duration")

        self._build_button(
            duration_row,
            "−",
            lambda: self._change_duration(-1)
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        duration_entry = tk.Entry(
            duration_row,
            textvariable=self.duration_var,
            justify="center",
            font=("Arial", 16, "bold"),
            relief="flat",
            bd=0,
            insertbackground=self.colors["text"],
            bg="#091017",
            fg=self.colors["text"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        duration_entry.grid(row=0, column=1, sticky="ew", padx=6, ipady=9)
        duration_entry.bind("<Return>", lambda _event: self._apply_duration())

        self._build_button(
            duration_row,
            "+",
            lambda: self._change_duration(1)
        ).grid(row=0, column=2, sticky="ew", padx=6)

        self._build_button(
            duration_row,
            "Apply",
            self._apply_duration
        ).grid(row=0, column=3, sticky="ew", padx=(6, 0))

        preset_row = tk.Frame(controls, bg=self.colors["card"])
        preset_row.pack(fill="x", pady=(0, 12))
        for column in range(3):
            preset_row.grid_columnconfigure(column, weight=1, uniform="detail-preset")

        for column, minutes in enumerate((15, 25, 50)):
            self._build_button(
                preset_row,
                f"{minutes}m",
                lambda value=minutes: self._apply_duration(value)
            ).grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 6, 0))

        action_row = tk.Frame(controls, bg=self.colors["card"])
        action_row.pack(fill="x")
        for column in range(5):
            action_row.grid_columnconfigure(column, weight=1)

        self._build_button(
            action_row,
            "Start",
            self.callbacks["start"],
            bg=self.colors["accent"],
            fg="#17120D"
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._build_button(
            action_row,
            "Pause",
            self.callbacks["pause"],
            bg=self.colors["warning"],
            fg="#17120D"
        ).grid(row=0, column=1, sticky="ew", padx=6)
        self._build_button(
            action_row,
            "Resume",
            self.callbacks["resume"],
            bg=self.colors["teal"],
            fg="#062323"
        ).grid(row=0, column=2, sticky="ew", padx=6)
        self._build_button(
            action_row,
            "Stop",
            self.callbacks["stop"],
            bg=self.colors["danger"],
            fg="#2A0909"
        ).grid(row=0, column=3, sticky="ew", padx=6)
        self._build_button(
            action_row,
            "Reset",
            self.callbacks["reset"],
            bg="#1D2731",
            fg=self.colors["text"]
        ).grid(row=0, column=4, sticky="ew", padx=(6, 0))

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
            cursor="hand2"
        )

    def _change_duration(self, delta):
        try:
            current = int(self.duration_var.get().strip())
        except ValueError:
            current = 25
        self.duration_var.set(str(max(1, min(current + delta, 180))))

    def _apply_duration(self, minutes=None):
        if minutes is None:
            value = self.duration_var.get().strip()
        else:
            value = str(minutes)
            self.duration_var.set(value)
        self.callbacks["apply_duration"](value)

    def update_state(self, timer_text, current_seconds, total_seconds, status, task_name, duration_minutes):
        self.duration_var.set(str(duration_minutes))
        self.task_label.config(text=f"Task: {task_name}")
        self.timer_label.config(text=timer_text)

        progress = 1 - (current_seconds / max(total_seconds, 1))
        progress = min(max(progress, 0), 1)
        self.timer_canvas.itemconfig(self.timer_arc, extent=-progress * 360)

        status_colors = {
            "ready": self.colors["text"],
            "running": self.colors["teal"],
            "paused": self.colors["warning"],
            "finished": self.colors["success"],
        }
        status_messages = {
            "ready": "Ready to begin.",
            "running": "Stay focused.",
            "paused": "Paused. Resume when ready.",
            "finished": "Session complete.",
        }

        self.status_label.config(
            text=status.title(),
            fg=status_colors.get(status, self.colors["text"])
        )
        self.hint_label.config(text=status_messages.get(status, "Stay focused."))
