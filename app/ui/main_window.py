import calendar
import time
import tkinter as tk
from datetime import datetime, timedelta

from PIL import Image, ImageTk
import cv2
import pyautogui

from app.core.camera import Camera
from app.core.hand_detector import HandDetector
from app.core.gesture_classifier import GestureClassifier
from app.core.gesture_state import GestureState
from app.core.confirmation_manager import ConfirmationManager
from app.core.virtual_mouse import VirtualMouse

from app.features.study_timer import StudyTimer
from app.features.session_logger import SessionLogger
from app.features.task_manager import TaskManager

from app.ui.activity_detail_window import ActivityDetailView
from app.ui.assistive_touch_cursor import AssistiveTouchCursor
from app.ui.pomodoro_detail_window import PomodoroDetailView
from app.ui.sessions_window import SessionsWindow
from app.ui.study_progress_detail_window import StudyProgressDetailView

pyautogui.FAILSAFE = False
DEBUG_HITBOX_CLICKS = True
INTERACTIVE_WIDGET_CLASSES = {"Button", "Entry", "Text", "TEntry", "Treeview"}

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Study OS")
        self.root.geometry("1480x920")
        self.root.minsize(1320, 820)
        self.root.configure(bg="#05070B")

        self.colors = {
            "bg": "#05070B",
            "panel": "#0B0F14",
            "card": "#11161D",
            "card_alt": "#0D1218",
            "border": "#5A3817",
            "accent": "#FFB347",
            "accent_bright": "#FFC766",
            "accent_soft": "#2B1C0A",
            "teal": "#42E8E0",
            "teal_soft": "#10373A",
            "text": "#F5E8CF",
            "muted": "#B9A68B",
            "subtle": "#7E6F5C",
            "success": "#63E6BE",
            "warning": "#FF9B54",
            "danger": "#FF6B6B",
        }

        self.camera = Camera(camera_index=0)
        self.hand_detector = HandDetector(max_num_hands=2)
        self.gesture_classifier = GestureClassifier()

        self.left_state = GestureState(required_frames=8)
        self.right_state = GestureState(required_frames=8)

        self.confirmation_manager = ConfirmationManager(timeout_seconds=3)
        self.study_timer = StudyTimer(study_minutes=25)
        self.timer_duration_var = tk.StringVar(
            value=str(self.study_timer.get_duration_minutes())
        )
        self.session_logger = SessionLogger()
        self.task_manager = TaskManager()

        self.previous_requested_action = None
        self.previous_left_gesture = None
        self.previous_right_gesture = None

        self.session_start_datetime = None
        self.pause_started_at = None
        self.total_paused_seconds = 0
        self.pause_count = 0
        self.session_saved = False

        self.camera_image = None
        self.virtual_mouse_mode = False
        self.virtual_mouse = None
        self.last_metrics_refresh = 0
        self.pomodoro_detail_view = None
        self.activity_detail_view = None
        self.study_progress_detail_view = None
        self.pending_activity_task_selection = None
        self.update_after_id = None

        self._build_ui()
        self.assistive_touch_cursor = AssistiveTouchCursor(self.root)
        self._refresh_dashboard_metrics(force=True)
        self._start_camera()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        self.main_container = tk.Frame(self.root, bg=self.colors["bg"])
        self.main_container.pack(fill="both", expand=True, padx=24, pady=24)

        self.detail_container = tk.Frame(self.root, bg=self.colors["bg"])

        self.sidebar = tk.Frame(
            self.main_container,
            bg=self.colors["panel"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=18,
            pady=20
        )
        self.sidebar.pack(side="left", fill="y", padx=(0, 18))

        self.content = tk.Frame(self.main_container, bg=self.colors["bg"])
        self.content.pack(side="left", fill="both", expand=True)

        for column in range(3):
            self.content.grid_columnconfigure(column, weight=1, uniform="content")

        self.content.grid_rowconfigure(0, weight=3)
        self.content.grid_rowconfigure(1, weight=2)
        self.content.grid_rowconfigure(2, weight=2)

        self._build_sidebar()
        self._build_timer_card()
        self._build_activity_card()
        self._build_goals_card()
        self._build_calendar_card()
        self._build_streak_card()
        self._build_controls_card()
        self._build_camera_card()

    def _build_sidebar(self):
        logo_frame = tk.Frame(self.sidebar, bg=self.colors["panel"])
        logo_frame.pack(fill="x", pady=(0, 24))

        logo_badge = tk.Canvas(
            logo_frame,
            width=90,
            height=90,
            bg=self.colors["panel"],
            highlightthickness=0
        )
        logo_badge.pack()
        logo_badge.create_oval(12, 12, 78, 78, outline=self.colors["accent"], width=2)
        logo_badge.create_text(
            45,
            45,
            text="◎",
            fill=self.colors["accent_bright"],
            font=("Arial", 28, "bold")
        )

        tk.Label(
            logo_frame,
            text="STUDY OS",
            font=("Arial", 20, "bold"),
            bg=self.colors["panel"],
            fg=self.colors["text"]
        ).pack(pady=(12, 4))

        tk.Label(
            logo_frame,
            text="v2.4",
            font=("Arial", 10),
            bg=self.colors["panel"],
            fg=self.colors["muted"]
        ).pack()

        nav_items = [
            ("Dashboard", True),
            ("Focus", False),
            ("Tasks", False),
            ("Notes", False),
            ("Analytics", False),
            ("Calendar", False),
            ("Settings", False),
        ]

        nav_frame = tk.Frame(self.sidebar, bg=self.colors["panel"])
        nav_frame.pack(fill="x", pady=(8, 22))

        for label, is_active in nav_items:
            item_bg = self.colors["accent_soft"] if is_active else self.colors["panel"]
            item_fg = self.colors["accent_bright"] if is_active else self.colors["text"]
            border = self.colors["accent"] if is_active else self.colors["panel"]

            tk.Label(
                nav_frame,
                text=label,
                anchor="w",
                padx=14,
                pady=10,
                font=("Arial", 12, "bold" if is_active else "normal"),
                bg=item_bg,
                fg=item_fg,
                highlightbackground=border,
                highlightthickness=1 if is_active else 0
            ).pack(fill="x", pady=4)

        quote_card = tk.Frame(
            self.sidebar,
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=16,
            pady=16
        )
        quote_card.pack(fill="x", side="bottom")

        tk.Label(
            quote_card,
            text="Discipline today\nSuccess tomorrow.",
            justify="left",
            font=("Arial", 12),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(anchor="w")

    def _build_timer_card(self):
        self.timer_body = self._create_card(
            "POMODORO TIMER",
            row=0,
            column=0,
            columnspan=2
        )

        header_row = tk.Frame(self.timer_body, bg=self.colors["card"])
        header_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            header_row,
            text="Deep Focus",
            bg=self.colors["accent_soft"],
            fg=self.colors["accent_bright"],
            font=("Arial", 11, "bold"),
            padx=14,
            pady=6
        ).pack(side="right")

        timer_content = tk.Frame(self.timer_body, bg=self.colors["card"])
        timer_content.pack(fill="both", expand=True)

        dial_panel = tk.Frame(timer_content, bg=self.colors["card"])
        dial_panel.pack(side="left", fill="both", expand=True)

        controls_panel = tk.Frame(
            timer_content,
            bg=self.colors["card_alt"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=14,
            pady=14
        )
        controls_panel.pack(side="right", fill="y", padx=(20, 0))

        self._build_timer_display(dial_panel)
        self._build_timer_controls_panel(controls_panel)
        self.timer_card = self.timer_body.master
        self._bind_timer_detail_trigger(self.timer_card)

    def _bind_timer_detail_trigger(self, widget):
        self._register_detail_trigger(
            widget,
            self.open_pomodoro_detail,
            "open_pomodoro_detail",
        )

    def _bind_activity_detail_trigger(self, widget):
        self._register_detail_trigger(
            widget,
            self.open_activity_detail,
            "open_activity_detail",
        )

    def _bind_study_progress_detail_trigger(self, widget):
        self._register_detail_trigger(
            widget,
            self.open_study_progress_detail,
            "open_study_progress_detail",
        )

    def _register_detail_trigger(self, widget, callback, action_name):
        if widget.winfo_class() not in INTERACTIVE_WIDGET_CLASSES:
            self._set_hitbox_action(widget, callback, action_name)

        try:
            widget.configure(cursor="hand2")
        except tk.TclError:
            pass

        for child in widget.winfo_children():
            self._register_detail_trigger(child, callback, action_name)

    def _set_virtual_click_metadata(self, widget, callback, action_name):
        setattr(widget, "_virtual_click_action", callback)
        setattr(widget, "_virtual_click_name", action_name)

    def _set_hitbox_action(self, widget, callback, action_name):
        self._set_virtual_click_metadata(widget, callback, action_name)
        widget.bind(
            "<Button-1>",
            lambda _event, bound_callback=callback, bound_name=action_name, bound_widget=widget:
                self._run_hitbox_action(bound_callback, bound_name, bound_widget)
        )

    def _register_virtual_button_targets(self, widget):
        try:
            widget_class = widget.winfo_class()
        except tk.TclError:
            return

        if widget_class == "Button":
            try:
                label = widget.cget("text").strip()
            except tk.TclError:
                label = ""
            action_name = f"button:{label}" if label else "button"
            self._set_virtual_click_metadata(widget, widget.invoke, action_name)

        for child in widget.winfo_children():
            self._register_virtual_button_targets(child)

    def _run_hitbox_action(self, callback, action_name, widget):
        if DEBUG_HITBOX_CLICKS:
            print(
                f"[hitbox-click] action={action_name} "
                f"widget={widget.winfo_class()} name={widget.winfo_name()}"
            )
        callback()

    def _resolve_hitbox_action(self, widget):
        current = widget
        while current is not None:
            callback = getattr(current, "_virtual_click_action", None)
            action_name = getattr(current, "_virtual_click_name", None)
            if callable(callback):
                return current, callback, action_name or callback.__name__
            current = current.master
        return None, None, None

    def _resolve_invokable_widget(self, widget):
        current = widget
        while current is not None:
            invoke = getattr(current, "invoke", None)
            if callable(invoke):
                return current, invoke
            current = current.master
        return None, None

    def _point_in_widget(self, widget, screen_x, screen_y):
        try:
            if not widget.winfo_exists() or not widget.winfo_ismapped():
                return False
        except tk.TclError:
            return False

        left = widget.winfo_rootx()
        top = widget.winfo_rooty()
        right = left + widget.winfo_width()
        bottom = top + widget.winfo_height()
        return left <= screen_x <= right and top <= screen_y <= bottom

    def _get_active_detail_view(self):
        for view in (
            self.pomodoro_detail_view,
            self.activity_detail_view,
            self.study_progress_detail_view,
        ):
            try:
                if view is not None and view.winfo_exists() and view.winfo_ismapped():
                    return view
            except tk.TclError:
                continue
        return None

    def _resolve_virtual_action_at(self, widget, screen_x, screen_y):
        try:
            if not widget.winfo_exists() or not widget.winfo_ismapped():
                return None, None, None
        except tk.TclError:
            return None, None, None

        for child in reversed(widget.winfo_children()):
            resolved_widget, callback, action_name = self._resolve_virtual_action_at(
                child,
                screen_x,
                screen_y,
            )
            if callback is not None:
                return resolved_widget, callback, action_name

        if not self._point_in_widget(widget, screen_x, screen_y):
            return None, None, None

        callback = getattr(widget, "_virtual_click_action", None)
        action_name = getattr(widget, "_virtual_click_name", None)
        if callable(callback):
            return widget, callback, action_name or callback.__name__

        return None, None, None

    def _build_timer_display(self, parent):
        self.timer_canvas = tk.Canvas(
            parent,
            width=280,
            height=280,
            bg=self.colors["card"],
            highlightthickness=0
        )
        self.timer_canvas.pack(expand=True, pady=(8, 0))

        self.timer_canvas.create_oval(
            30,
            30,
            250,
            250,
            outline="#2A2118",
            width=14
        )
        self.timer_arc = self.timer_canvas.create_arc(
            30,
            30,
            250,
            250,
            start=90,
            extent=0,
            style="arc",
            outline=self.colors["accent"],
            width=14
        )

        timer_info = tk.Frame(self.timer_canvas, bg=self.colors["card"])
        self.timer_canvas.create_window(140, 140, window=timer_info)

        tk.Label(
            timer_info,
            text="FOCUS SESSION",
            font=("Arial", 12),
            bg=self.colors["card"],
            fg=self.colors["muted"]
        ).pack(pady=(0, 8))

        self.timer_label = tk.Label(
            timer_info,
            text=f"{self.study_timer.get_duration_minutes():02d}:00",
            font=("Arial", 44, "bold"),
            bg=self.colors["card"],
            fg=self.colors["accent_bright"]
        )
        self.timer_label.pack()

        self.status_label = tk.Label(
            timer_info,
            text="Ready",
            font=("Arial", 15),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        self.status_label.pack(pady=(8, 4))

        self.timer_hint_label = tk.Label(
            timer_info,
            text="Stay focused.",
            font=("Arial", 11),
            bg=self.colors["card"],
            fg=self.colors["teal"]
        )
        self.timer_hint_label.pack()

    def _build_timer_controls_panel(self, parent):
        tk.Label(
            parent,
            text="Duration (minutes)",
            font=("Arial", 10, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["muted"]
        ).pack(anchor="w")

        duration_row = tk.Frame(parent, bg=self.colors["card_alt"])
        duration_row.pack(fill="x", pady=(10, 12))
        for column in range(4):
            duration_row.grid_columnconfigure(column, weight=1, uniform="timer-duration")

        self._build_timer_control_button(
            duration_row,
            "−",
            lambda: self.adjust_timer_duration(-1),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.duration_entry = tk.Entry(
            duration_row,
            textvariable=self.timer_duration_var,
            width=4,
            justify="center",
            font=("Arial", 12, "bold"),
            relief="flat",
            bd=0,
            insertbackground=self.colors["text"],
            bg="#091017",
            fg=self.colors["text"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        self.duration_entry.grid(row=0, column=1, sticky="ew", padx=6, ipady=7)
        self.duration_entry.bind(
            "<Return>",
            lambda _event: self.apply_timer_duration()
        )

        self._build_timer_control_button(
            duration_row,
            "+",
            lambda: self.adjust_timer_duration(1),
        ).grid(row=0, column=2, sticky="ew", padx=6)

        self._build_timer_control_button(
            duration_row,
            "Apply",
            self.apply_timer_duration,
        ).grid(row=0, column=3, sticky="ew", padx=(6, 0))

        preset_row = tk.Frame(parent, bg=self.colors["card_alt"])
        preset_row.pack(fill="x", pady=(0, 14))
        for column in range(3):
            preset_row.grid_columnconfigure(column, weight=1, uniform="timer-preset")

        for column, minutes in enumerate((15, 25, 50)):
            self._build_timer_control_button(
                preset_row,
                f"{minutes}m",
                lambda value=minutes: self.apply_timer_duration(value)
            ).grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 6, 0))

        self.timer_control_note = tk.Label(
            parent,
            text="Open the detailed timer view to use playback controls.",
            font=("Arial", 9),
            bg=self.colors["card_alt"],
            fg=self.colors["subtle"],
            wraplength=260,
            justify="left"
        )
        self.timer_control_note.pack(anchor="w", pady=(10, 0))

    def _build_activity_card(self):
        self.activity_body = self._create_card(
            "ACTIVITY MONITOR",
            row=0,
            column=2
        )

        stats_row = tk.Frame(self.activity_body, bg=self.colors["card"])
        stats_row.pack(fill="x", pady=(0, 14))

        self.pending_tasks_value = self._build_stat_block(
            stats_row,
            "Pending",
            "0",
            self.colors["teal"]
        )
        self.completed_tasks_value = self._build_stat_block(
            stats_row,
            "Tasks Completed",
            "0",
            self.colors["accent"]
        )
        self.due_today_value = self._build_stat_block(
            stats_row,
            "Due Today",
            "0",
            self.colors["success"]
        )

        self.activity_summary_label = tk.Label(
            self.activity_body,
            text="Open the activity monitor to manage tasks and due dates.",
            font=("Arial", 10),
            bg=self.colors["card"],
            fg=self.colors["muted"],
            anchor="w",
            justify="left",
        )
        self.activity_summary_label.pack(fill="x", pady=(0, 10))

        self.activity_preview_frame = tk.Frame(
            self.activity_body,
            bg=self.colors["card_alt"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=12,
            pady=12,
        )
        self.activity_preview_frame.pack(fill="x", pady=(0, 10))

        self.activity_preview_title = tk.Label(
            self.activity_preview_frame,
            text="Upcoming Tasks",
            font=("Arial", 11, "bold"),
            bg=self.colors["card_alt"],
            fg=self.colors["accent_bright"],
            anchor="w",
        )
        self.activity_preview_title.pack(fill="x", pady=(0, 8))

        self.activity_preview_labels = []
        for _ in range(3):
            label = tk.Label(
                self.activity_preview_frame,
                text="",
                font=("Arial", 10),
                bg=self.colors["card_alt"],
                fg=self.colors["text"],
                anchor="w",
                justify="left",
            )
            label.pack(fill="x", pady=2)
            self.activity_preview_labels.append(label)

        self.chart_canvas = tk.Canvas(
            self.activity_body,
            height=170,
            bg=self.colors["card_alt"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        self.chart_canvas.pack(fill="both", expand=True, pady=(4, 0))
        self.activity_card = self.activity_body.master
        self._bind_activity_detail_trigger(self.activity_card)

    def _build_goals_card(self):
        self.goals_body = self._create_card(
            "STUDY GOALS",
            row=1,
            column=0
        )

        goal_layout = tk.Frame(self.goals_body, bg=self.colors["card"])
        goal_layout.pack(fill="both", expand=True, pady=(2, 0))

        self.goal_canvas = tk.Canvas(
            goal_layout,
            width=156,
            height=156,
            bg=self.colors["card"],
            highlightthickness=0
        )
        self.goal_canvas.pack(side="left", padx=(0, 16), pady=(2, 0))
        self.goal_canvas.create_oval(
            20,
            20,
            136,
            136,
            outline=self.colors["teal_soft"],
            width=10
        )
        self.goal_arc = self.goal_canvas.create_arc(
            20,
            20,
            136,
            136,
            start=90,
            extent=0,
            style="arc",
            outline=self.colors["teal"],
            width=10
        )

        goal_info = tk.Frame(goal_layout, bg=self.colors["card"])
        goal_info.pack(side="left", fill="both", expand=True)

        tk.Label(
            goal_info,
            text="Weekly Study Goal",
            font=("Arial", 12),
            bg=self.colors["card"],
            fg=self.colors["muted"]
        ).pack(anchor="w")

        self.goal_target_label = tk.Label(
            goal_info,
            text="25h 00m",
            font=("Arial", 20, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        self.goal_target_label.pack(anchor="w", pady=(4, 12))

        self.goal_progress_track = tk.Canvas(
            goal_info,
            width=240,
            height=12,
            bg=self.colors["card"],
            highlightthickness=0
        )
        self.goal_progress_track.pack(anchor="w")
        self.goal_progress_track.create_rectangle(
            0,
            2,
            240,
            10,
            fill="#1D252D",
            outline=""
        )
        self.goal_progress_fill = self.goal_progress_track.create_rectangle(
            0,
            2,
            0,
            10,
            fill=self.colors["teal"],
            outline=""
        )

        self.goal_studied_label = tk.Label(
            goal_info,
            text="Time Studied: 0h 00m",
            font=("Arial", 11),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        self.goal_studied_label.pack(anchor="w", pady=(12, 4))

        self.goal_message_label = tk.Label(
            goal_info,
            text="Keep going.",
            font=("Arial", 10),
            bg=self.colors["card"],
            fg=self.colors["accent_bright"],
            wraplength=240,
            justify="left"
        )
        self.goal_message_label.pack(anchor="w")
        self.goals_card = self.goals_body.master
        self._bind_study_progress_detail_trigger(self.goals_card)

    def _build_calendar_card(self):
        self.calendar_body = self._create_card(
            "CALENDAR",
            row=1,
            column=1
        )

        self.calendar_month_label = tk.Label(
            self.calendar_body,
            text="",
            font=("Arial", 13, "bold"),
            bg=self.colors["card"],
            fg=self.colors["accent_bright"]
        )
        self.calendar_month_label.pack(anchor="center", pady=(0, 10))

        self.calendar_grid = tk.Frame(self.calendar_body, bg=self.colors["card"])
        self.calendar_grid.pack(fill="both", expand=True)
        self._render_calendar()

    def _build_streak_card(self):
        self.streak_body = self._create_card(
            "FOCUS STREAK",
            row=1,
            column=2
        )

        self.streak_value_label = tk.Label(
            self.streak_body,
            text="0",
            font=("Arial", 54, "bold"),
            bg=self.colors["card"],
            fg=self.colors["accent_bright"]
        )
        self.streak_value_label.pack(anchor="w", pady=(20, 0))

        tk.Label(
            self.streak_body,
            text="Days",
            font=("Arial", 18),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(anchor="w")

        self.streak_subtitle_label = tk.Label(
            self.streak_body,
            text="No sessions logged yet.",
            font=("Arial", 12),
            bg=self.colors["card"],
            fg=self.colors["teal"]
        )
        self.streak_subtitle_label.pack(anchor="w", pady=(18, 4))

        self.streak_best_label = tk.Label(
            self.streak_body,
            text="Best streak: 0 days",
            font=("Arial", 11),
            bg=self.colors["card"],
            fg=self.colors["muted"]
        )
        self.streak_best_label.pack(anchor="w")

    def _build_controls_card(self):
        self.controls_body = self._create_card(
            "SESSION CONTROLS",
            row=2,
            column=0,
            columnspan=2
        )

        task_frame = tk.Frame(self.controls_body, bg=self.colors["card"])
        task_frame.pack(fill="x", pady=(0, 18))

        tk.Label(
            task_frame,
            text="Current Task",
            font=("Arial", 12),
            bg=self.colors["card"],
            fg=self.colors["muted"]
        ).pack(anchor="w", pady=(0, 6))

        self.task_entry = tk.Entry(
            task_frame,
            font=("Arial", 14),
            relief="flat",
            bd=0,
            insertbackground=self.colors["text"],
            bg="#0A1016",
            fg=self.colors["text"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        self.task_entry.pack(fill="x", ipady=10)
        self.task_entry.insert(0, "Study Session")

        tk.Label(
            self.controls_body,
            text="Timer playback and duration controls are in the Pomodoro card above.",
            font=("Arial", 11),
            bg=self.colors["card"],
            fg=self.colors["subtle"]
        ).pack(anchor="w", pady=(0, 16))

        utility_frame = tk.Frame(self.controls_body, bg=self.colors["card"])
        utility_frame.pack(fill="x", pady=(0, 18))

        self._build_secondary_button(
            utility_frame,
            "Save Session",
            self.save_current_session
        ).pack(side="left", padx=(0, 10))

        self._build_secondary_button(
            utility_frame,
            "View Study Sessions",
            self.open_sessions_window
        ).pack(side="left", padx=(0, 10))

        self.mouse_mode_button = self._build_secondary_button(
            utility_frame,
            "Mouse Mode: Off",
            self.toggle_virtual_mouse_mode
        )
        self.mouse_mode_button.pack(side="left")

        self.confirm_label = tk.Label(
            self.controls_body,
            text="No action pending",
            font=("Arial", 12, "bold"),
            bg=self.colors["card"],
            fg=self.colors["muted"],
            anchor="w",
            justify="left"
        )
        self.confirm_label.pack(fill="x", pady=(0, 8))

        self.help_label = tk.Label(
            self.controls_body,
            text=(
                "Mouse mode uses the right hand for cursor movement and pinch to click. "
                "Pinch with middle, ring, and pinky extended, then move them up or down to scroll. "
                "Turn it off for gesture mode: right open palm + left fist = start/resume, "
                "both fists = pause, right pointing + left fist = stop, "
                "right peace + left fist = reset."
            ),
            font=("Arial", 11),
            wraplength=760,
            justify="left",
            bg=self.colors["card"],
            fg=self.colors["subtle"]
        )
        self.help_label.pack(anchor="w")

    def _build_camera_card(self):
        self.camera_body = self._create_card(
            "CAMERA + GESTURES",
            row=2,
            column=2
        )

        self.camera_label = tk.Label(
            self.camera_body,
            bg="#05070B",
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        self.camera_label.pack(fill="both", expand=True, pady=(0, 16))

        gesture_row = tk.Frame(self.camera_body, bg=self.colors["card"])
        gesture_row.pack(fill="x")

        self.left_gesture_label = tk.Label(
            gesture_row,
            text="Left: no_hand",
            font=("Arial", 11),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        self.left_gesture_label.pack(side="left")

        self.right_gesture_label = tk.Label(
            gesture_row,
            text="Right: no_hand",
            font=("Arial", 11),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        self.right_gesture_label.pack(side="right")

    def _create_card(self, title, row, column, columnspan=1, rowspan=1):
        card = tk.Frame(
            self.content,
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=18,
            pady=16
        )
        card.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            rowspan=rowspan,
            sticky="nsew",
            padx=10,
            pady=10
        )

        header = tk.Frame(card, bg=self.colors["card"])
        header.pack(fill="x", pady=(0, 12))

        tk.Label(
            header,
            text=title,
            font=("Arial", 16, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(side="left")

        body = tk.Frame(card, bg=self.colors["card"])
        body.pack(fill="both", expand=True)
        return body

    def _build_stat_block(self, parent, label, value, accent):
        block = tk.Frame(parent, bg=self.colors["card"])
        block.pack(side="left", fill="x", expand=True)

        tk.Label(
            block,
            text=label,
            font=("Arial", 11),
            bg=self.colors["card"],
            fg=self.colors["muted"]
        ).pack(anchor="w")

        value_label = tk.Label(
            block,
            text=value,
            font=("Arial", 24, "bold"),
            bg=self.colors["card"],
            fg=accent
        )
        value_label.pack(anchor="w", pady=(4, 0))
        return value_label

    def _build_action_button(self, parent, text, bg, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Arial", 12, "bold"),
            relief="flat",
            bd=0,
            padx=18,
            pady=10,
            bg=bg,
            fg="#17120D",
            activebackground=bg,
            activeforeground="#17120D",
            cursor="hand2"
        )

    def _build_secondary_button(self, parent, text, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Arial", 11),
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            bg="#0A1016",
            fg=self.colors["text"],
            activebackground="#131B24",
            activeforeground=self.colors["text"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            cursor="hand2"
        )

    def _build_timer_control_button(
        self,
        parent,
        text,
        command,
        bg=None,
        fg=None,
        width=8
    ):
        button_bg = bg or "#121B24"
        button_fg = fg or self.colors["text"]

        return tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            font=("Arial", 10, "bold"),
            relief="flat",
            bd=0,
            padx=8,
            pady=6,
            bg=button_bg,
            fg=button_fg,
            activebackground=button_bg,
            activeforeground=button_fg,
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            cursor="hand2"
        )

    def _render_calendar(self):
        for child in self.calendar_grid.winfo_children():
            child.destroy()

        today = datetime.now()
        year = today.year
        month = today.month
        self.calendar_month_label.config(text=today.strftime("%B %Y"))

        weekdays = ["S", "M", "T", "W", "T", "F", "S"]
        for index, label in enumerate(weekdays):
            tk.Label(
                self.calendar_grid,
                text=label,
                width=3,
                font=("Arial", 10, "bold"),
                bg=self.colors["card"],
                fg=self.colors["muted"]
            ).grid(row=0, column=index, padx=4, pady=4)

        for row_index, week in enumerate(calendar.monthcalendar(year, month), start=1):
            for column_index, day in enumerate(week):
                if day == 0:
                    cell_text = ""
                    bg = self.colors["card"]
                    fg = self.colors["subtle"]
                else:
                    cell_text = str(day)
                    if day == today.day:
                        bg = self.colors["accent"]
                        fg = "#1A1208"
                    else:
                        bg = self.colors["card"]
                        fg = self.colors["text"]

                tk.Label(
                    self.calendar_grid,
                    text=cell_text,
                    width=3,
                    font=("Arial", 10),
                    bg=bg,
                    fg=fg
                ).grid(row=row_index, column=column_index, padx=4, pady=4)

    def _start_camera(self):
        try:
            self.camera.open()
            self.update_loop()
        except RuntimeError as error:
            self.confirm_label.config(text=str(error), fg=self.colors["danger"])

    def _clear_session_state(self):
        self.session_start_datetime = None
        self.pause_started_at = None
        self.total_paused_seconds = 0
        self.pause_count = 0
        self.session_saved = False

    def toggle_virtual_mouse_mode(self):
        self.virtual_mouse_mode = not self.virtual_mouse_mode
        self.mouse_mode_button.config(
            text=f"Mouse Mode: {'On' if self.virtual_mouse_mode else 'Off'}"
        )

        if self.virtual_mouse_mode:
            self.root.configure(cursor="")
        else:
            self.assistive_touch_cursor.hide()

    def _get_requested_duration_minutes(self):
        raw_value = self.timer_duration_var.get().strip()

        try:
            minutes = int(raw_value)
        except ValueError:
            self.confirm_label.config(
                text="Enter a whole number of minutes.",
                fg=self.colors["danger"]
            )
            return None

        minutes = max(1, min(minutes, 180))
        self.timer_duration_var.set(str(minutes))
        return minutes

    def adjust_timer_duration(self, delta):
        current_minutes = self._get_requested_duration_minutes()
        if current_minutes is None:
            return

        self.apply_timer_duration(current_minutes + delta)

    def apply_timer_duration(self, minutes=None):
        if self.study_timer.get_status() == "running":
            self.confirm_label.config(
                text="Pause or reset the timer before changing duration.",
                fg=self.colors["warning"]
            )
            return

        if minutes is None:
            minutes = self._get_requested_duration_minutes()
        else:
            minutes = max(1, min(int(minutes), 180))
            self.timer_duration_var.set(str(minutes))

        if minutes is None:
            return

        self.study_timer.set_duration_minutes(minutes)
        self._clear_session_state()

        current_seconds = self.study_timer.update()
        self.timer_label.config(
            text=f"{current_seconds // 60:02d}:{current_seconds % 60:02d}"
        )
        self._update_timer_visuals(current_seconds)
        self.confirm_label.config(
            text=f"Pomodoro duration set to {minutes} minutes.",
            fg=self.colors["success"]
        )
        self._sync_pomodoro_detail_window()

    def get_requested_action(self, right_gesture):
        status = self.study_timer.get_status()

        if right_gesture == "open_palm":
            if status == "ready":
                return "start"

            if status == "paused":
                return "resume"

        if right_gesture == "peace":
            return "reset"

        if right_gesture == "pointing":
            return "stop"

        return None

    def handle_gesture_controls(self, stable_left_gesture, stable_right_gesture):
        self.confirmation_manager.update()

        both_fists = (
            stable_left_gesture == "fist"
            and stable_right_gesture == "fist"
        )
        both_fists_just_happened = (
            both_fists
            and not (
                self.previous_left_gesture == "fist"
                and self.previous_right_gesture == "fist"
            )
        )

        if both_fists_just_happened:
            self.confirmation_manager.clear()
            self.previous_requested_action = None
            self.run_confirmed_action("pause")
            self.previous_left_gesture = stable_left_gesture
            self.previous_right_gesture = stable_right_gesture
            return

        requested_action = self.get_requested_action(stable_right_gesture)
        right_gesture_just_changed = (
            stable_right_gesture != self.previous_right_gesture
        )

        if requested_action is not None:
            if (
                requested_action != self.previous_requested_action
                and right_gesture_just_changed
            ):
                self.confirmation_manager.request_action(requested_action)
                self.previous_requested_action = requested_action

        if requested_action is None:
            self.previous_requested_action = None

        left_fist_just_happened = (
            stable_left_gesture == "fist"
            and self.previous_left_gesture != "fist"
        )

        if left_fist_just_happened and self.confirmation_manager.has_pending_action():
            confirmed_action = self.confirmation_manager.confirm()
            self.run_confirmed_action(confirmed_action)
            self.previous_requested_action = None

        self.previous_left_gesture = stable_left_gesture
        self.previous_right_gesture = stable_right_gesture

    def run_confirmed_action(self, action):
        if action == "start":
            self.start_session()
        elif action == "resume":
            self.resume_session()
        elif action == "pause":
            self.pause_session()
        elif action == "stop":
            self.stop_session()
        elif action == "reset":
            self.reset_session()

    def start_session(self):
        if self.study_timer.get_status() == "ready":
            self.study_timer.start()
            self.session_start_datetime = datetime.now()
            self.total_paused_seconds = 0
            self.pause_count = 0
            self.pause_started_at = None
            self.session_saved = False

    def pause_session(self):
        if self.study_timer.get_status() == "running":
            self.study_timer.pause()
            self.pause_started_at = time.time()
            self.pause_count += 1

    def resume_session(self):
        if self.study_timer.get_status() == "paused":
            if self.pause_started_at is not None:
                self.total_paused_seconds += time.time() - self.pause_started_at
                self.pause_started_at = None

            self.study_timer.resume()

    def stop_session(self):
        if self.study_timer.get_status() in ["running", "paused"]:
            self.study_timer.stop()
            self.save_current_session("stopped")

    def reset_session(self):
        self.study_timer.reset()
        self._clear_session_state()

    def save_current_session(self, status="manual_saved"):
        if self.session_saved:
            self.confirm_label.config(
                text="Session already saved.",
                fg=self.colors["muted"]
            )
            return

        if self.session_start_datetime is None:
            self.confirm_label.config(
                text="No session has started yet.",
                fg=self.colors["danger"]
            )
            return

        end_datetime = datetime.now()

        duration_seconds = (
            end_datetime - self.session_start_datetime
        ).total_seconds() - self.total_paused_seconds

        if duration_seconds < 0:
            duration_seconds = 0

        duration_minutes = round(duration_seconds / 60, 2)

        task_name = self.task_entry.get().strip()
        if not task_name:
            task_name = "Untitled Study Session"

        self.session_logger.save_session(
            task_name=task_name,
            start_time=self.session_start_datetime.strftime("%H:%M:%S"),
            end_time=end_datetime.strftime("%H:%M:%S"),
            duration_minutes=duration_minutes,
            status=status,
            pauses=self.pause_count
        )

        self.session_saved = True
        self.confirm_label.config(
            text="Session saved to CSV.",
            fg=self.colors["success"]
        )
        self._refresh_dashboard_metrics(force=True)

    def open_sessions_window(self):
        SessionsWindow(self.root, self.session_logger)

    def _show_detail_view(self, active_view):
        self.main_container.pack_forget()

        for view in (
            self.pomodoro_detail_view,
            self.activity_detail_view,
            self.study_progress_detail_view,
        ):
            if view is not None and view is not active_view:
                view.pack_forget()

        self.detail_container.pack(fill="both", expand=True, padx=24, pady=24)
        active_view.pack(fill="both", expand=True)

    def open_pomodoro_detail(self):
        callbacks = {
            "start": lambda: self.run_confirmed_action("start"),
            "pause": lambda: self.run_confirmed_action("pause"),
            "resume": lambda: self.run_confirmed_action("resume"),
            "stop": lambda: self.run_confirmed_action("stop"),
            "reset": lambda: self.run_confirmed_action("reset"),
            "apply_duration": self.apply_timer_duration,
            "back": self.close_pomodoro_detail,
        }

        if self.pomodoro_detail_view is None:
            self.pomodoro_detail_view = PomodoroDetailView(
                self.detail_container,
                self.colors,
                callbacks
            )
            self._register_virtual_button_targets(self.pomodoro_detail_view)

        self._show_detail_view(self.pomodoro_detail_view)
        self._sync_pomodoro_detail_window()

    def close_pomodoro_detail(self):
        if self.pomodoro_detail_view is not None:
            self.pomodoro_detail_view.pack_forget()
        self.detail_container.pack_forget()
        self.main_container.pack(fill="both", expand=True, padx=24, pady=24)
        self._refresh_dashboard_metrics(force=True)
        self._sync_pomodoro_detail_window()

    def open_activity_detail(self, task_id=None):
        callbacks = {
            "add": self.add_activity_task,
            "complete": lambda task_id: self.update_activity_task_status(task_id, "completed"),
            "reopen": lambda task_id: self.update_activity_task_status(task_id, "pending"),
            "delete": self.delete_activity_task,
            "back": self.close_activity_detail,
        }

        if self.activity_detail_view is None:
            self.activity_detail_view = ActivityDetailView(
                self.detail_container,
                self.colors,
                callbacks,
            )
            self._register_virtual_button_targets(self.activity_detail_view)

        self.pending_activity_task_selection = None if task_id is None else str(task_id)
        self._show_detail_view(self.activity_detail_view)
        self._sync_activity_detail_window()

    def close_activity_detail(self):
        if self.activity_detail_view is not None:
            self.activity_detail_view.pack_forget()
        self.detail_container.pack_forget()
        self.main_container.pack(fill="both", expand=True, padx=24, pady=24)
        self._refresh_dashboard_metrics(force=True)

    def open_study_progress_detail(self):
        callbacks = {
            "back": self.close_study_progress_detail,
        }

        if self.study_progress_detail_view is None:
            self.study_progress_detail_view = StudyProgressDetailView(
                self.detail_container,
                self.colors,
                callbacks,
            )
            self._register_virtual_button_targets(self.study_progress_detail_view)

        self._show_detail_view(self.study_progress_detail_view)
        self._sync_study_progress_detail_window()

    def close_study_progress_detail(self):
        if self.study_progress_detail_view is not None:
            self.study_progress_detail_view.pack_forget()
        self.detail_container.pack_forget()
        self.main_container.pack(fill="both", expand=True, padx=24, pady=24)
        self._refresh_dashboard_metrics(force=True)

    def add_activity_task(self, task_data):
        if self.activity_detail_view is None:
            return

        title = task_data["title"].strip()
        due_date = task_data["due_date"].strip()
        due_time = task_data["due_time"].strip()
        notes = task_data["notes"].strip()

        if not title:
            self.activity_detail_view.set_feedback(
                "Enter a task title before saving.",
                "danger",
            )
            return

        try:
            datetime.strptime(due_date, "%Y-%m-%d")
            datetime.strptime(due_time, "%H:%M")
        except ValueError:
            self.activity_detail_view.set_feedback(
                "Use YYYY-MM-DD for date and HH:MM for time.",
                "danger",
            )
            return

        self.task_manager.add_task(
            title=title,
            due_date=due_date,
            due_time=due_time,
            notes=notes,
        )
        self.activity_detail_view.clear_form()
        self.activity_detail_view.set_feedback(
            "Task saved to the activity monitor.",
            "success",
        )
        self._sync_activity_detail_window()
        self._refresh_dashboard_metrics(force=True)

    def update_activity_task_status(self, task_id, status):
        if self.activity_detail_view is None:
            return

        if task_id is None:
            self.activity_detail_view.set_feedback(
                "Select a task first.",
                "warning",
            )
            return

        updated = self.task_manager.update_task_status(task_id, status)
        if not updated:
            self.activity_detail_view.set_feedback(
                "The selected task could not be updated.",
                "danger",
            )
            return

        action_text = "completed" if status == "completed" else "reopened"
        self.activity_detail_view.set_feedback(
            f"Task {action_text}.",
            "success",
        )
        self._sync_activity_detail_window()
        self._refresh_dashboard_metrics(force=True)

    def delete_activity_task(self, task_id):
        if self.activity_detail_view is None:
            return

        if task_id is None:
            self.activity_detail_view.set_feedback(
                "Select a task first.",
                "warning",
            )
            return

        deleted = self.task_manager.delete_task(task_id)
        if not deleted:
            self.activity_detail_view.set_feedback(
                "The selected task could not be deleted.",
                "danger",
            )
            return

        self.activity_detail_view.set_feedback(
            "Task deleted.",
            "success",
        )
        self._sync_activity_detail_window()
        self._refresh_dashboard_metrics(force=True)

    def _sync_activity_detail_window(self):
        if self.activity_detail_view is None:
            return

        self.activity_detail_view.set_tasks(self.task_manager.read_tasks())
        if self.pending_activity_task_selection is not None:
            self.activity_detail_view.select_task(self.pending_activity_task_selection)
            self.pending_activity_task_selection = None

    def _sync_study_progress_detail_window(self):
        if self.study_progress_detail_view is None:
            return

        self.study_progress_detail_view.update_state(
            self._calculate_metrics(),
            self._format_minutes,
        )

    def _sync_pomodoro_detail_window(self):
        if self.pomodoro_detail_view is None:
            return

        current_seconds = self.study_timer.update()
        timer_text = f"{current_seconds // 60:02d}:{current_seconds % 60:02d}"
        task_name = self.task_entry.get().strip() or "Study Session"
        self.pomodoro_detail_view.update_state(
            timer_text=timer_text,
            current_seconds=current_seconds,
            total_seconds=int(self.study_timer.study_seconds),
            status=self.study_timer.get_status(),
            task_name=task_name,
            duration_minutes=self.study_timer.get_duration_minutes()
        )

    def _ensure_virtual_mouse(self, frame):
        if self.virtual_mouse is not None:
            return

        frame_h, frame_w = frame.shape[:2]
        self.root.update_idletasks()

        self.virtual_mouse = VirtualMouse(
            screen_w=max(1, self.root.winfo_width()),
            screen_h=max(1, self.root.winfo_height()),
            frame_w=frame_w,
            frame_h=frame_h,
            move_mouse=False,
            mirror_x=False,
            preferred_hand_label="Right",
            fallback_to_any_hand=False,
            click_handler=lambda x, y: self.root.after(0, self._dispatch_virtual_click, x, y)
        )

    def _update_virtual_mouse(self, frame):
        self._ensure_virtual_mouse(frame)
        self.virtual_mouse.set_output_size(
            max(1, self.root.winfo_width()),
            max(1, self.root.winfo_height())
        )

        mouse_x, mouse_y, clicked, scroll_delta = self.virtual_mouse.process(frame)

        self._move_system_cursor(mouse_x, mouse_y)

        self.assistive_touch_cursor.update_cursor(
            mouse_x,
            mouse_y,
            self.virtual_mouse.last_pinch_ratio,
            clicked
        )

        if scroll_delta != 0:
            self.root.after(0, self._dispatch_virtual_scroll, mouse_x, mouse_y, scroll_delta)

    def _move_system_cursor(self, x, y):
        screen_x = self.root.winfo_rootx() + x
        screen_y = self.root.winfo_rooty() + y

        try:
            pyautogui.moveTo(screen_x, screen_y, _pause=False)
        except Exception as error:
            self.confirm_label.config(
                text=f"Mouse mode cannot move the system cursor: {error}",
                fg=self.colors["warning"],
            )

    def _dispatch_virtual_click(self, x, y):
        self.root.update_idletasks()

        try:
            pointer_x, pointer_y = pyautogui.position()
            screen_x = int(pointer_x)
            screen_y = int(pointer_y)
        except Exception:
            screen_x = self.root.winfo_rootx() + x
            screen_y = self.root.winfo_rooty() + y

        if self.main_container.winfo_ismapped():
            if self._point_in_widget(self.timer_card, screen_x, screen_y):
                if DEBUG_HITBOX_CLICKS:
                    print(
                        f"[virtual-hitbox] action=open_pomodoro_detail "
                        f"card=timer screen=({screen_x},{screen_y})"
                    )
                self.open_pomodoro_detail()
                return

            if self._point_in_widget(self.activity_card, screen_x, screen_y):
                if DEBUG_HITBOX_CLICKS:
                    print(
                        f"[virtual-hitbox] action=open_activity_detail "
                        f"card=activity screen=({screen_x},{screen_y})"
                    )
                self.open_activity_detail()
                return

            if self._point_in_widget(self.goals_card, screen_x, screen_y):
                if DEBUG_HITBOX_CLICKS:
                    print(
                        f"[virtual-hitbox] action=open_study_progress_detail "
                        f"card=goals screen=({screen_x},{screen_y})"
                    )
                self.open_study_progress_detail()
                return

        active_detail_view = self._get_active_detail_view()
        if active_detail_view is not None:
            hitbox_widget, hitbox_callback, action_name = self._resolve_virtual_action_at(
                active_detail_view,
                screen_x,
                screen_y,
            )
            if hitbox_callback is not None:
                if DEBUG_HITBOX_CLICKS:
                    print(
                        f"[virtual-hitbox] action={action_name} "
                        f"widget={hitbox_widget.winfo_class()} name={hitbox_widget.winfo_name()} "
                        f"screen=({screen_x},{screen_y})"
                    )
                hitbox_callback()
                return

        target = self.root.winfo_containing(screen_x, screen_y)
        if target is None:
            try:
                pyautogui.click(screen_x, screen_y)
            except Exception as error:
                self.confirm_label.config(
                    text=f"Mouse mode cannot click the system cursor: {error}",
                    fg=self.colors["warning"],
                )
            return

        local_x = screen_x - target.winfo_rootx()
        local_y = screen_y - target.winfo_rooty()

        hitbox_widget, hitbox_callback, action_name = self._resolve_hitbox_action(target)
        if hitbox_callback is not None:
            if DEBUG_HITBOX_CLICKS:
                print(
                    f"[virtual-click] action={action_name} "
                    f"target={target.winfo_class()} name={target.winfo_name()} "
                    f"resolved={hitbox_widget.winfo_class()} resolved_name={hitbox_widget.winfo_name()} "
                    f"screen=({screen_x},{screen_y}) local=({local_x},{local_y})"
                )
            hitbox_callback()
            return

        invokable_widget, invoke = self._resolve_invokable_widget(target)
        if invoke is not None:
            if DEBUG_HITBOX_CLICKS:
                print(
                    f"[virtual-invoke] "
                    f"target={target.winfo_class()} name={target.winfo_name()} "
                    f"resolved={invokable_widget.winfo_class()} resolved_name={invokable_widget.winfo_name()} "
                    f"screen=({screen_x},{screen_y}) local=({local_x},{local_y})"
                )
            try:
                invoke()
                return
            except tk.TclError:
                pass

        try:
            if not target.winfo_exists():
                return
            target.focus_set()
        except tk.TclError:
            pass

        for sequence in ("<Enter>", "<Motion>", "<ButtonPress-1>", "<ButtonRelease-1>"):
            try:
                target.event_generate(sequence, x=local_x, y=local_y, when="tail")
            except tk.TclError:
                break

    def _dispatch_virtual_scroll(self, x, y, delta):
        screen_x = self.root.winfo_rootx() + x
        screen_y = self.root.winfo_rooty() + y
        target = self.root.winfo_containing(screen_x, screen_y)

        while target is not None:
            local_x = screen_x - target.winfo_rootx()
            local_y = screen_y - target.winfo_rooty()

            try:
                target.focus_set()
            except tk.TclError:
                pass

            yview_scroll = getattr(target, "yview_scroll", None)
            if callable(yview_scroll):
                try:
                    target.yview_scroll(-1 if delta > 0 else 1, "units")
                    return
                except tk.TclError:
                    pass

            try:
                target.event_generate(
                    "<MouseWheel>",
                    delta=delta,
                    x=local_x,
                    y=local_y,
                    when="tail"
                )
                if delta > 0:
                    target.event_generate("<Button-4>", x=local_x, y=local_y, when="tail")
                else:
                    target.event_generate("<Button-5>", x=local_x, y=local_y, when="tail")
                return
            except tk.TclError:
                target = target.master

    def _refresh_dashboard_metrics(self, force=False):
        current_time = time.time()
        if not force and current_time - self.last_metrics_refresh < 5:
            return

        self.last_metrics_refresh = current_time
        metrics = self._calculate_metrics()
        task_metrics = self._calculate_task_metrics()

        self.pending_tasks_value.config(text=str(task_metrics["pending_tasks"]))
        self.completed_tasks_value.config(text=str(task_metrics["completed_tasks"]))
        self.due_today_value.config(text=str(task_metrics["due_today"]))
        self.activity_summary_label.config(text=task_metrics["summary"])
        self._update_activity_preview(task_metrics["preview_tasks"])
        self._draw_activity_chart(
            task_metrics["labels"],
            task_metrics["created_counts"],
            task_metrics["completed_counts"],
        )
        self.streak_value_label.config(text=str(metrics["current_streak"]))
        self.streak_subtitle_label.config(text=metrics["streak_message"])
        self.streak_best_label.config(text=f"Best streak: {metrics['best_streak']} days")
        self.goal_studied_label.config(
            text=f"Time Studied: {self._format_minutes(metrics['weekly_minutes'])}"
        )
        self.goal_message_label.config(text=metrics["goal_message"])

        goal_ratio = min(metrics["weekly_minutes"] / metrics["goal_minutes"], 1.0)
        self.goal_canvas.itemconfig(self.goal_arc, extent=-goal_ratio * 360)
        self.goal_canvas.delete("goal_text")
        self.goal_canvas.create_text(
            78,
            68,
            text=f"{int(goal_ratio * 100)}%",
            tags="goal_text",
            fill=self.colors["accent_bright"],
            font=("Arial", 20, "bold")
        )
        self.goal_canvas.create_text(
            78,
            92,
            text="WEEKLY GOAL",
            tags="goal_text",
            fill=self.colors["muted"],
            font=("Arial", 9, "bold")
        )
        self.goal_progress_track.coords(
            self.goal_progress_fill,
            0,
            2,
            int(240 * goal_ratio),
            10
        )
        self._sync_study_progress_detail_window()

    def _calculate_metrics(self):
        sessions = self.session_logger.read_sessions()
        today = datetime.now().date()
        start_date = today - timedelta(days=6)

        dates_in_range = [start_date + timedelta(days=index) for index in range(7)]
        minutes_by_day = {day: 0.0 for day in dates_in_range}
        sessions_by_day = {day: 0 for day in dates_in_range}
        session_dates = []
        ordered_sessions = []

        for session in sessions:
            raw_date = session.get("date", "")
            try:
                session_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError:
                continue

            session_dates.append(session_date)
            ordered_sessions.append((self._parse_session_datetime(session), session))
            try:
                duration = float(session.get("duration_minutes", 0) or 0)
            except ValueError:
                duration = 0

            if session_date in minutes_by_day:
                minutes_by_day[session_date] += duration
                sessions_by_day[session_date] += 1

        weekly_minutes = sum(minutes_by_day.values())
        weekly_sessions = sum(sessions_by_day.values())
        goal_minutes = 25 * 60
        goal_ratio = weekly_minutes / goal_minutes if goal_minutes else 0
        focus_score = min(99, int(goal_ratio * 70 + min(weekly_sessions, 12) * 2.5))

        current_streak = self._compute_current_streak(set(session_dates), today)
        best_streak = self._compute_best_streak(set(session_dates))
        days_with_sessions = sum(1 for count in sessions_by_day.values() if count > 0)

        if goal_ratio >= 1:
            goal_message = "Weekly goal reached."
        elif goal_ratio >= 0.7:
            goal_message = "Strong pace this week."
        elif goal_ratio >= 0.4:
            goal_message = "Good start. Keep the streak alive."
        else:
            goal_message = "Build momentum with one more session."

        if current_streak == 0:
            streak_message = "Start a streak with today's first session."
        elif current_streak == 1:
            streak_message = "1 day active. Repeat tomorrow."
        else:
            streak_message = f"{current_streak} straight study days."

        recent_sessions = []
        for _, session in sorted(
            ordered_sessions,
            key=lambda item: item[0] or datetime.min,
            reverse=True,
        )[:8]:
            recent_sessions.append(
                {
                    "date": session.get("date", ""),
                    "task_name": session.get("task_name", "Study Session"),
                    "duration_minutes": session.get("duration_minutes", "0"),
                    "status": session.get("status", "ready"),
                    "pauses": session.get("pauses", "0"),
                }
            )

        return {
            "weekly_minutes": weekly_minutes,
            "weekly_sessions": weekly_sessions,
            "goal_minutes": goal_minutes,
            "focus_score": focus_score,
            "current_streak": current_streak,
            "best_streak": best_streak,
            "goal_message": goal_message,
            "streak_message": streak_message,
            "day_labels": [day.strftime("%a") for day in dates_in_range],
            "day_minutes": [minutes_by_day[day] for day in dates_in_range],
            "day_sessions": [sessions_by_day[day] for day in dates_in_range],
            "days_with_sessions": days_with_sessions,
            "recent_sessions": recent_sessions,
            "total_sessions": len(sessions),
        }

    def _calculate_task_metrics(self):
        tasks = self.task_manager.read_tasks()
        today = datetime.now().date()
        start_date = today - timedelta(days=6)
        dates_in_range = [start_date + timedelta(days=index) for index in range(7)]
        created_by_day = {day: 0 for day in dates_in_range}
        completed_by_day = {day: 0 for day in dates_in_range}

        pending_tasks = 0
        completed_tasks = 0
        due_today = 0
        overdue_tasks = 0
        next_due_text = None

        for task in tasks:
            created_at = self._parse_iso_datetime(task.get("created_at", ""))
            if created_at is not None and created_at.date() in created_by_day:
                created_by_day[created_at.date()] += 1

            completed_at = self._parse_iso_datetime(task.get("completed_at", ""))
            if completed_at is not None and completed_at.date() in completed_by_day:
                completed_by_day[completed_at.date()] += 1

            due_at = self._parse_due_datetime(task)
            is_completed = task.get("status") == "completed"

            if is_completed:
                completed_tasks += 1
            else:
                pending_tasks += 1

                if due_at is not None:
                    if due_at.date() == today:
                        due_today += 1
                    if due_at.date() < today:
                        overdue_tasks += 1
                    if next_due_text is None:
                        next_due_text = due_at.strftime("%Y-%m-%d %H:%M")

        if pending_tasks == 0 and completed_tasks == 0:
            summary = "No activity tasks yet. Open the card to add your first one."
        elif overdue_tasks > 0:
            summary = f"{overdue_tasks} overdue task{'s' if overdue_tasks != 1 else ''}. Next due: {next_due_text or 'n/a'}."
        elif next_due_text is not None:
            summary = f"Next due: {next_due_text}. {pending_tasks} pending task{'s' if pending_tasks != 1 else ''}."
        else:
            summary = f"All current tasks are complete. {completed_tasks} finished so far."

        labels = [day.strftime("%a") for day in dates_in_range]
        created_counts = [created_by_day[day] for day in dates_in_range]
        completed_counts = [completed_by_day[day] for day in dates_in_range]
        preview_tasks = []

        for task in tasks:
            if task.get("status") == "completed" and pending_tasks > 0:
                continue
            preview_tasks.append(task)
            if len(preview_tasks) == 3:
                break

        return {
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks,
            "due_today": due_today,
            "summary": summary,
            "labels": labels,
            "created_counts": created_counts,
            "completed_counts": completed_counts,
            "preview_tasks": preview_tasks,
        }

    def _compute_current_streak(self, session_dates, today):
        streak = 0
        cursor = today

        while cursor in session_dates:
            streak += 1
            cursor -= timedelta(days=1)

        return streak

    def _compute_best_streak(self, session_dates):
        if not session_dates:
            return 0

        ordered_dates = sorted(session_dates)
        best = 1
        current = 1

        for previous, current_date in zip(ordered_dates, ordered_dates[1:]):
            if current_date == previous + timedelta(days=1):
                current += 1
                best = max(best, current)
            else:
                current = 1

        return best

    def _parse_iso_datetime(self, value):
        if not value:
            return None

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _parse_due_datetime(self, task):
        try:
            return datetime.strptime(
                f"{task.get('due_date', '')} {task.get('due_time', '')}",
                "%Y-%m-%d %H:%M",
            )
        except ValueError:
            return None

    def _parse_session_datetime(self, session):
        try:
            return datetime.strptime(
                f"{session.get('date', '')} {session.get('start_time', '00:00:00')}",
                "%Y-%m-%d %H:%M:%S",
            )
        except ValueError:
            return None

    def _draw_activity_chart(self, labels, created_counts, completed_counts):
        self.chart_canvas.delete("all")

        width = max(self.chart_canvas.winfo_width(), 420)
        height = max(self.chart_canvas.winfo_height(), 220)
        left = 44
        top = 20
        right = width - 18
        bottom = height - 34

        self.chart_canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            outline="",
            fill=self.colors["card_alt"]
        )

        max_value = max(
            max(created_counts, default=0),
            max(completed_counts, default=0),
            1,
        )
        max_value = max(5, int(max_value + 1))

        for index in range(6):
            y = top + ((bottom - top) / 5) * index
            value = max_value - ((max_value / 5) * index)
            self.chart_canvas.create_line(
                left,
                y,
                right,
                y,
                fill="#22303B"
            )
            self.chart_canvas.create_text(
                left - 12,
                y,
                text=f"{value:.0f}",
                fill=self.colors["muted"],
                font=("Arial", 9)
            )

        step_x = (right - left) / max(len(labels) - 1, 1)
        pending_points = []
        completed_points = []

        for index, label in enumerate(labels):
            x = left + step_x * index
            self.chart_canvas.create_text(
                x,
                bottom + 16,
                text=label,
                fill=self.colors["muted"],
                font=("Arial", 9)
            )

            pending_y = bottom - ((created_counts[index] / max_value) * (bottom - top))
            completed_y = bottom - ((completed_counts[index] / max_value) * (bottom - top))
            pending_points.extend([x, pending_y])
            completed_points.extend([x, completed_y])

            self.chart_canvas.create_oval(
                x - 3,
                pending_y - 3,
                x + 3,
                pending_y + 3,
                fill=self.colors["teal"],
                outline=self.colors["teal"]
            )
            self.chart_canvas.create_oval(
                x - 3,
                completed_y - 3,
                x + 3,
                completed_y + 3,
                fill=self.colors["accent"],
                outline=self.colors["accent"]
            )

        if len(pending_points) >= 4:
            self.chart_canvas.create_line(
                *pending_points,
                fill=self.colors["teal"],
                width=2,
                smooth=True
            )
            self.chart_canvas.create_line(
                *completed_points,
                fill=self.colors["accent"],
                width=2,
                smooth=True
            )

        legend_y = height - 12
        self.chart_canvas.create_oval(18, legend_y - 4, 26, legend_y + 4, fill=self.colors["teal"], outline="")
        self.chart_canvas.create_text(56, legend_y, text="Tasks Added", fill=self.colors["teal"], font=("Arial", 9), anchor="center")
        self.chart_canvas.create_oval(144, legend_y - 4, 152, legend_y + 4, fill=self.colors["accent"], outline="")
        self.chart_canvas.create_text(201, legend_y, text="Tasks Completed", fill=self.colors["accent"], font=("Arial", 9), anchor="center")

    def _update_activity_preview(self, tasks):
        if not tasks:
            self.activity_preview_title.config(text="Upcoming Tasks")
            self.activity_preview_labels[0].config(
                text="No tasks yet. Open Activity Monitor to add one.",
                fg=self.colors["muted"],
            )
            for label in self.activity_preview_labels[1:]:
                label.config(text="", fg=self.colors["text"])
            return

        pending_count = sum(1 for task in tasks if task.get("status") != "completed")
        if pending_count > 0:
            self.activity_preview_title.config(text="Upcoming Tasks")
        else:
            self.activity_preview_title.config(text="Recent Completed Tasks")

        for index, label in enumerate(self.activity_preview_labels):
            if index >= len(tasks):
                label.config(text="", fg=self.colors["text"])
                label.unbind("<Button-1>")
                setattr(label, "_virtual_click_action", None)
                setattr(label, "_virtual_click_name", None)
                continue

            task = tasks[index]
            status_prefix = "Done" if task.get("status") == "completed" else "Due"
            due_text = f"{task.get('due_date', '')} {task.get('due_time', '')}".strip()
            if not due_text:
                due_text = "No due date"

            task_id = str(task.get("task_id", ""))
            label.config(
                text=f"{task.get('title', 'Untitled Task')}  |  {status_prefix}: {due_text}",
                fg=self.colors["text"] if task.get("status") != "completed" else self.colors["muted"],
            )
            self._set_hitbox_action(
                label,
                lambda selected_task_id=task_id: self.open_activity_detail(selected_task_id),
                f"open_activity_detail:{task_id}",
            )
            try:
                label.configure(cursor="hand2")
            except tk.TclError:
                pass

    def _format_minutes(self, minutes):
        total_minutes = int(round(minutes))
        hours = total_minutes // 60
        remainder = total_minutes % 60
        return f"{hours}h {remainder:02d}m"

    def _update_timer_visuals(self, current_seconds):
        total_seconds = max(int(self.study_timer.study_seconds), 1)
        progress = 1 - (current_seconds / total_seconds)
        progress = min(max(progress, 0), 1)

        self.timer_canvas.itemconfig(self.timer_arc, extent=-progress * 360)

        status = self.study_timer.get_status()
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

        self.status_label.config(text=status.title(), fg=status_colors.get(status, self.colors["text"]))
        self.timer_hint_label.config(text=status_messages.get(status, "Stay focused."))

    def update_loop(self):
        frame = self.camera.read_frame()

        if frame is not None:
            frame = cv2.flip(frame, 1)
            if self.virtual_mouse_mode:
                self._update_virtual_mouse(frame)
            else:
                self.assistive_touch_cursor.hide()

            results = self.hand_detector.detect_hands(frame)
            frame = self.hand_detector.draw_landmarks(frame, results)

            hands_data = self.hand_detector.get_all_hand_positions(frame, results)

            raw_left_gesture = "no_hand"
            raw_right_gesture = "no_hand"

            for hand in hands_data:
                label = hand["label"]
                landmarks = hand["landmarks"]
                gesture = self.gesture_classifier.classify(landmarks)

                if label == "Left":
                    raw_left_gesture = gesture
                elif label == "Right":
                    raw_right_gesture = gesture

            stable_left_gesture = self.left_state.update(raw_left_gesture)
            stable_right_gesture = self.right_state.update(raw_right_gesture)

            self.handle_gesture_controls(stable_left_gesture, stable_right_gesture)

            self.left_gesture_label.config(text=f"Left: {stable_left_gesture}")
            self.right_gesture_label.config(text=f"Right: {stable_right_gesture}")

            current_seconds = self.study_timer.update()
            minutes = current_seconds // 60
            seconds = current_seconds % 60
            timer_text = f"{minutes:02d}:{seconds:02d}"

            self.timer_label.config(text=timer_text)
            self._update_timer_visuals(current_seconds)
            self._sync_pomodoro_detail_window()

            confirm_message = self.confirmation_manager.get_message()
            if confirm_message is not None:
                self.confirm_label.config(text=confirm_message, fg=self.colors["warning"])
            elif not self.session_saved:
                self.confirm_label.config(text="No action pending", fg=self.colors["muted"])

            preview_frame = cv2.resize(frame, (360, 220))
            preview_frame = cv2.cvtColor(preview_frame, cv2.COLOR_BGR2RGB)

            image = Image.fromarray(preview_frame)
            self.camera_image = ImageTk.PhotoImage(image=image)
            self.camera_label.config(image=self.camera_image)

            self._refresh_dashboard_metrics()

        self.update_after_id = self.root.after(15, self.update_loop)

    def on_close(self):
        if self.update_after_id is not None:
            self.root.after_cancel(self.update_after_id)
            self.update_after_id = None
        self.camera.release()
        self.hand_detector.close()
        if self.virtual_mouse is not None:
            self.virtual_mouse.close()
        self.assistive_touch_cursor.destroy()
        self.root.destroy()
