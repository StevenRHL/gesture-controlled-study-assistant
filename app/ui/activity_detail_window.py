import tkinter as tk
from tkinter import ttk


class ActivityDetailView(tk.Frame):
    def __init__(self, parent, colors, callbacks):
        super().__init__(parent, bg=colors["bg"])
        self.colors = colors
        self.callbacks = callbacks
        self.tasks_by_id = {}
        self.editing_task_id = None

        self.title_var = tk.StringVar()
        self.due_date_var = tk.StringVar()
        self.due_time_var = tk.StringVar()
        self.submit_button_var = tk.StringVar(value="Add Task")
        self.clear_button_var = tk.StringVar(value="Clear")

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
            text="ACTIVITY MONITOR",
            font=("Arial", 24, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"],
        ).pack(side="left", padx=(18, 0))

        tk.Label(
            header,
            text="Task Planner",
            font=("Arial", 12, "bold"),
            bg=self.colors["accent_soft"],
            fg=self.colors["accent_bright"],
            padx=14,
            pady=8,
        ).pack(side="right")

        form_card = tk.Frame(
            container,
            bg=self.colors["card_alt"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=18,
            pady=18,
        )
        form_card.pack(fill="x", pady=(0, 18))

        tk.Label(
            form_card,
            text="Add Task",
            font=("Arial", 16, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["text"],
        ).pack(anchor="w", pady=(0, 12))

        title_row = tk.Frame(form_card, bg=self.colors["card_alt"])
        title_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            title_row,
            text="Task",
            font=("Arial", 11, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["muted"],
            width=10,
            anchor="w",
        ).pack(side="left")

        self.title_entry = tk.Entry(
            title_row,
            textvariable=self.title_var,
            font=("Arial", 13),
            relief="flat",
            bd=0,
            insertbackground=self.colors["text"],
            bg="#091017",
            fg=self.colors["text"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
        )
        self.title_entry.pack(side="left", fill="x", expand=True, ipady=10)

        schedule_row = tk.Frame(form_card, bg=self.colors["card_alt"])
        schedule_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            schedule_row,
            text="Due Date",
            font=("Arial", 11, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["muted"],
            width=10,
            anchor="w",
        ).pack(side="left")

        self.due_date_entry = tk.Entry(
            schedule_row,
            textvariable=self.due_date_var,
            font=("Arial", 12),
            relief="flat",
            bd=0,
            insertbackground=self.colors["text"],
            bg="#091017",
            fg=self.colors["text"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
        )
        self.due_date_entry.pack(side="left", fill="x", expand=True, ipady=10)

        tk.Label(
            schedule_row,
            text="Due Time",
            font=("Arial", 11, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["muted"],
            width=10,
            anchor="w",
        ).pack(side="left", padx=(18, 0))

        self.due_time_entry = tk.Entry(
            schedule_row,
            textvariable=self.due_time_var,
            font=("Arial", 12),
            relief="flat",
            bd=0,
            insertbackground=self.colors["text"],
            bg="#091017",
            fg=self.colors["text"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            width=14,
        )
        self.due_time_entry.pack(side="left", ipady=10)

        hint_row = tk.Frame(form_card, bg=self.colors["card_alt"])
        hint_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            hint_row,
            text="Use YYYY-MM-DD for date and HH:MM for time.",
            font=("Arial", 10),
            bg=self.colors["card_alt"],
            fg=self.colors["subtle"],
        ).pack(anchor="w")

        tk.Label(
            form_card,
            text="Notes",
            font=("Arial", 11, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["muted"],
        ).pack(anchor="w", pady=(0, 6))

        self.notes_text = tk.Text(
            form_card,
            height=5,
            wrap="word",
            font=("Arial", 12),
            relief="flat",
            bd=0,
            insertbackground=self.colors["text"],
            bg="#091017",
            fg=self.colors["text"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
        )
        self.notes_text.pack(fill="x", expand=True, pady=(0, 12))

        action_row = tk.Frame(form_card, bg=self.colors["card_alt"])
        action_row.pack(fill="x")
        for column in range(6):
            action_row.grid_columnconfigure(column, weight=1, uniform="activity-actions")

        self._build_button(
            action_row,
            self.submit_button_var,
            self._handle_submit_task,
            bg=self.colors["accent"],
            fg="#17120D",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._build_button(
            action_row,
            self.clear_button_var,
            self.clear_form,
            bg="#1D2731",
        ).grid(row=0, column=1, sticky="ew", padx=6)
        self._build_button(
            action_row,
            "Edit Selected",
            self._handle_edit_task,
            bg="#243240",
        ).grid(row=0, column=2, sticky="ew", padx=6)
        self._build_button(
            action_row,
            "Complete",
            self._handle_complete_task,
            bg=self.colors["success"],
            fg="#072018",
        ).grid(row=0, column=3, sticky="ew", padx=6)
        self._build_button(
            action_row,
            "Reopen",
            self._handle_reopen_task,
            bg=self.colors["teal"],
            fg="#062323",
        ).grid(row=0, column=4, sticky="ew", padx=6)
        self._build_button(
            action_row,
            "Delete",
            self._handle_delete_task,
            bg=self.colors["danger"],
            fg="#2A0909",
        ).grid(row=0, column=5, sticky="ew", padx=(6, 0))

        self.feedback_label = tk.Label(
            form_card,
            text="Add tasks with a due date, due time, and notes.",
            font=("Arial", 11),
            bg=self.colors["card_alt"],
            fg=self.colors["muted"],
            anchor="w",
            justify="left",
        )
        self.feedback_label.pack(fill="x", pady=(12, 0))

        tasks_card = tk.Frame(
            container,
            bg=self.colors["card_alt"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=18,
            pady=18,
        )
        tasks_card.pack(fill="both", expand=True)

        tasks_header = tk.Frame(tasks_card, bg=self.colors["card_alt"])
        tasks_header.pack(fill="x", pady=(0, 12))

        tk.Label(
            tasks_header,
            text="Task List",
            font=("Arial", 16, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["text"],
        ).pack(side="left")

        self.task_count_label = tk.Label(
            tasks_header,
            text="0 tasks",
            font=("Arial", 11),
            bg=self.colors["card_alt"],
            fg=self.colors["accent_bright"],
        )
        self.task_count_label.pack(side="right")

        table_frame = tk.Frame(tasks_card, bg=self.colors["card_alt"])
        table_frame.pack(fill="both", expand=True)

        columns = ("task_id", "title", "due_date", "due_time", "status", "notes")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=10,
        )

        self.tree.heading("task_id", text="ID")
        self.tree.heading("title", text="Task")
        self.tree.heading("due_date", text="Due Date")
        self.tree.heading("due_time", text="Due Time")
        self.tree.heading("status", text="Status")
        self.tree.heading("notes", text="Notes")

        self.tree.column("task_id", width=55, anchor="center")
        self.tree.column("title", width=260)
        self.tree.column("due_date", width=110, anchor="center")
        self.tree.column("due_time", width=100, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("notes", width=360)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._handle_selection_change)

        tk.Label(
            tasks_card,
            text="Selected Task Notes",
            font=("Arial", 11, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["muted"],
        ).pack(anchor="w", pady=(14, 6))

        self.selected_notes_text = tk.Text(
            tasks_card,
            height=5,
            wrap="word",
            font=("Arial", 12),
            relief="flat",
            bd=0,
            state="disabled",
            bg="#091017",
            fg=self.colors["text"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
        )
        self.selected_notes_text.pack(fill="x", expand=False)

    def _build_button(self, parent, text, command, bg="#121B24", fg=None):
        button_options = {
            "command": command,
            "font": ("Arial", 12, "bold"),
            "relief": "flat",
            "bd": 0,
            "padx": 10,
            "pady": 10,
            "bg": bg,
            "fg": fg or self.colors["text"],
            "activebackground": bg,
            "activeforeground": fg or self.colors["text"],
            "highlightbackground": self.colors["border"],
            "highlightthickness": 1,
            "cursor": "hand2",
        }

        if isinstance(text, tk.StringVar):
            button_options["textvariable"] = text
        else:
            button_options["text"] = text

        return tk.Button(
            parent,
            **button_options,
        )

    def _handle_submit_task(self):
        task_data = self.get_form_data()
        if self.editing_task_id is None:
            self.callbacks["add"](task_data)
            return

        self.callbacks["update"](self.editing_task_id, task_data)

    def _handle_edit_task(self):
        task_id = self.get_selected_task_id()
        task = self.tasks_by_id.get(task_id)
        if task is None:
            self.set_feedback("Select a task first.", "warning")
            return

        self._load_task_into_form(task)
        self.set_feedback(
            f"Editing task #{task_id}. Save changes when ready.",
            "warning",
        )

    def _handle_complete_task(self):
        task_id = self.get_selected_task_id()
        self.callbacks["complete"](task_id)

    def _handle_reopen_task(self):
        task_id = self.get_selected_task_id()
        self.callbacks["reopen"](task_id)

    def _handle_delete_task(self):
        task_id = self.get_selected_task_id()
        self.callbacks["delete"](task_id)

    def _handle_selection_change(self, _event=None):
        task_id = self.get_selected_task_id()
        task = self.tasks_by_id.get(task_id)
        notes = task.get("notes", "") if task else ""
        self._set_selected_notes(notes or "No notes for this task.")

    def _set_selected_notes(self, text):
        self.selected_notes_text.configure(state="normal")
        self.selected_notes_text.delete("1.0", "end")
        self.selected_notes_text.insert("1.0", text)
        self.selected_notes_text.configure(state="disabled")

    def get_form_data(self):
        return {
            "title": self.title_var.get().strip(),
            "due_date": self.due_date_var.get().strip(),
            "due_time": self.due_time_var.get().strip(),
            "notes": self.notes_text.get("1.0", "end").strip(),
        }

    def get_selected_task_id(self):
        selection = self.tree.selection()
        if not selection:
            return None

        task_id = self.tree.item(selection[0], "values")[0]
        return str(task_id)

    def clear_form(self):
        self.editing_task_id = None
        self.submit_button_var.set("Add Task")
        self.clear_button_var.set("Clear")
        self.title_var.set("")
        self.due_date_var.set("")
        self.due_time_var.set("")
        self.notes_text.delete("1.0", "end")
        self.title_entry.focus_set()

    def select_task(self, task_id):
        if task_id is None:
            return

        task_id = str(task_id)
        if task_id not in self.tasks_by_id:
            return

        self.tree.selection_set(task_id)
        self.tree.focus(task_id)
        self.tree.see(task_id)
        self._handle_selection_change()

    def set_feedback(self, message, tone="muted"):
        tone_colors = {
            "muted": self.colors["muted"],
            "success": self.colors["success"],
            "warning": self.colors["warning"],
            "danger": self.colors["danger"],
        }
        self.feedback_label.config(
            text=message,
            fg=tone_colors.get(tone, self.colors["muted"]),
        )

    def set_tasks(self, tasks):
        selected_task_id = self.get_selected_task_id()
        self.tasks_by_id = {str(task["task_id"]): task for task in tasks}

        if self.editing_task_id is not None and self.editing_task_id not in self.tasks_by_id:
            self.clear_form()

        for item in self.tree.get_children():
            self.tree.delete(item)

        for task in tasks:
            self.tree.insert(
                "",
                "end",
                iid=str(task["task_id"]),
                values=(
                    task["task_id"],
                    task["title"],
                    task["due_date"],
                    task["due_time"],
                    task["status"].title(),
                    self._truncate_notes(task.get("notes", "")),
                ),
            )

        self.task_count_label.config(
            text=f"{len(tasks)} task{'s' if len(tasks) != 1 else ''}"
        )

        if selected_task_id and selected_task_id in self.tasks_by_id:
            self.tree.selection_set(selected_task_id)
            self.tree.focus(selected_task_id)
            self._handle_selection_change()
        elif tasks:
            first_task_id = str(tasks[0]["task_id"])
            self.tree.selection_set(first_task_id)
            self.tree.focus(first_task_id)
            self._handle_selection_change()
        else:
            self._set_selected_notes("No tasks added yet.")

    def _truncate_notes(self, notes):
        compact_notes = " ".join(notes.split())
        if len(compact_notes) <= 48:
            return compact_notes

        return f"{compact_notes[:45]}..."

    def _load_task_into_form(self, task):
        self.editing_task_id = str(task["task_id"])
        self.submit_button_var.set("Save Changes")
        self.clear_button_var.set("Cancel Edit")
        self.title_var.set(task.get("title", ""))
        self.due_date_var.set(task.get("due_date", ""))
        self.due_time_var.set(task.get("due_time", ""))
        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", task.get("notes", ""))
        self.title_entry.focus_set()
