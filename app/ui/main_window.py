import time
import tkinter as tk
from datetime import datetime
from PIL import Image, ImageTk
import cv2

from app.core.camera import Camera
from app.core.hand_detector import HandDetector
from app.core.gesture_classifier import GestureClassifier
from app.core.gesture_state import GestureState
from app.core.confirmation_manager import ConfirmationManager

from app.features.study_timer import StudyTimer
from app.features.session_logger import SessionLogger

from app.ui.sessions_window import SessionsWindow


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Gesture Study Tool")
        self.root.geometry("1100x650")
        self.root.configure(bg="#050505")

        self.camera = Camera(camera_index=0)
        self.hand_detector = HandDetector(max_num_hands=2)
        self.gesture_classifier = GestureClassifier()

        self.left_state = GestureState(required_frames=8)
        self.right_state = GestureState(required_frames=8)

        self.confirmation_manager = ConfirmationManager(timeout_seconds=3)
        self.study_timer = StudyTimer(study_minutes=1)
        self.session_logger = SessionLogger()

        self.previous_requested_action = None
        self.previous_left_gesture = None

        self.session_start_datetime = None
        self.pause_started_at = None
        self.total_paused_seconds = 0
        self.pause_count = 0
        self.session_saved = False

        self.camera_image = None

        self._build_ui()
        self._start_camera()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        main_container = tk.Frame(self.root, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        left_panel = tk.Frame(main_container, bg="#f5f5f5")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 20))

        right_panel = tk.Frame(main_container, bg="#f5f5f5")
        right_panel.pack(side="right", fill="y")

        title_label = tk.Label(
            left_panel,
            text="Gesture Study Tool",
            font=("Arial", 26, "bold"),
            bg="#FFFFFF"
        )
        title_label.pack(anchor="w", pady=(0, 20))

        task_frame = tk.Frame(left_panel, bg="#f5f5f5")
        task_frame.pack(anchor="w", pady=(0, 20))

        task_label = tk.Label(
            task_frame,
            text="Current Task:",
            font=("Arial", 14),
            bg="#f5f5f5"
        )
        task_label.pack(side="left", padx=(0, 10))

        self.task_entry = tk.Entry(
            task_frame,
            font=("Arial", 14),
            width=35
        )
        self.task_entry.pack(side="left")
        self.task_entry.insert(0, "Study Session")

        self.timer_label = tk.Label(
            left_panel,
            text="01:00",
            font=("Arial", 64, "bold"),
            bg="#f5f5f5",
            fg="#000000"
        )
        self.timer_label.pack(anchor="w", pady=(10, 0))

        self.status_label = tk.Label(
            left_panel,
            text="Status: Ready",
            font=("Arial", 18),
            bg="#ff0000"
        )
        self.status_label.pack(anchor="w", pady=(0, 20))

        self.confirm_label = tk.Label(
            left_panel,
            text="No action pending",
            font=("Arial", 16, "bold"),
            bg="#f5f5f5",
            fg="#555555"
        )
        self.confirm_label.pack(anchor="w", pady=(0, 25))

        button_frame = tk.Frame(left_panel, bg="#f5f5f5")
        button_frame.pack(anchor="w", pady=(0, 20))

        tk.Button(
            button_frame,
            text="Start",
            width=12,
            command=lambda: self.run_confirmed_action("start")
        ).grid(row=0, column=0, padx=5, pady=5)

        tk.Button(
            button_frame,
            text="Pause",
            width=12,
            command=lambda: self.run_confirmed_action("pause")
        ).grid(row=0, column=1, padx=5, pady=5)

        tk.Button(
            button_frame,
            text="Resume",
            width=12,
            command=lambda: self.run_confirmed_action("resume")
        ).grid(row=0, column=2, padx=5, pady=5)

        tk.Button(
            button_frame,
            text="Stop",
            width=12,
            command=lambda: self.run_confirmed_action("stop")
        ).grid(row=0, column=3, padx=5, pady=5)

        tk.Button(
            button_frame,
            text="Reset",
            width=12,
            command=lambda: self.run_confirmed_action("reset")
        ).grid(row=0, column=4, padx=5, pady=5)

        tk.Button(
            button_frame,
            text="Save Session",
            width=14,
            command=lambda: self.save_current_session("manual_saved")
        ).grid(row=1, column=0, padx=5, pady=5)

        tk.Button(
            button_frame,
            text="View Study Sessions",
            width=20,
            command=self.open_sessions_window
        ).grid(row=1, column=1, columnspan=2, padx=5, pady=5)

        help_text = (
            "Gestures: Right open palm = start/resume | "
            "Right fist = pause | Right peace = stop | "
            "Right pointing = reset | Left fist = confirm"
        )

        self.help_label = tk.Label(
            left_panel,
            text=help_text,
            font=("Arial", 11),
            bg="#f5f5f5",
            fg="#444444",
            wraplength=700,
            justify="left"
        )
        self.help_label.pack(anchor="w", pady=(20, 0))

        camera_title = tk.Label(
            right_panel,
            text="Camera Preview",
            font=("Arial", 16, "bold"),
            bg="#f5f5f5"
        )
        camera_title.pack(pady=(0, 10))

        self.camera_label = tk.Label(
            right_panel,
            bg="black",
            width=320,
            height=240
        )
        self.camera_label.pack()

        self.left_gesture_label = tk.Label(
            right_panel,
            text="Left: no_hand",
            font=("Arial", 12),
            bg="#f5f5f5"
        )
        self.left_gesture_label.pack(anchor="w", pady=(15, 0))

        self.right_gesture_label = tk.Label(
            right_panel,
            text="Right: no_hand",
            font=("Arial", 12),
            bg="#f5f5f5"
        )
        self.right_gesture_label.pack(anchor="w")

    def _start_camera(self):
        try:
            self.camera.open()
            self.update_loop()
        except RuntimeError as error:
            self.confirm_label.config(
                text=str(error),
                fg="red"
            )

    def get_requested_action(self, right_gesture):
        status = self.study_timer.get_status()

        if right_gesture == "open_palm":
            if status == "ready":
                return "start"

            if status == "paused":
                return "resume"

        if right_gesture == "fist":
            if status == "running":
                return "pause"

        if right_gesture == "peace":
            if status in ["running", "paused"]:
                return "stop"

        if right_gesture == "pointing":
            return "reset"

        return None

    def handle_gesture_controls(self, stable_left_gesture, stable_right_gesture):
        self.confirmation_manager.update()

        requested_action = self.get_requested_action(stable_right_gesture)

        if requested_action is not None:
            if requested_action != self.previous_requested_action:
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

        self.session_start_datetime = None
        self.pause_started_at = None
        self.total_paused_seconds = 0
        self.pause_count = 0
        self.session_saved = False

    def save_current_session(self, status):
        if self.session_saved:
            self.confirm_label.config(
                text="Session already saved.",
                fg="#555555"
            )
            return

        if self.session_start_datetime is None:
            self.confirm_label.config(
                text="No session has started yet.",
                fg="red"
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
            fg="green"
        )

    def open_sessions_window(self):
        SessionsWindow(self.root, self.session_logger)

    def update_loop(self):
        frame = self.camera.read_frame()

        if frame is not None:
            frame = cv2.flip(frame, 1)

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

            self.handle_gesture_controls(
                stable_left_gesture,
                stable_right_gesture
            )

            self.left_gesture_label.config(
                text=f"Left: {stable_left_gesture}"
            )

            self.right_gesture_label.config(
                text=f"Right: {stable_right_gesture}"
            )

            timer_text = self.study_timer.get_display_time()
            timer_status = self.study_timer.get_status()

            self.timer_label.config(text=timer_text)
            self.status_label.config(text=f"Status: {timer_status.title()}")

            confirm_message = self.confirmation_manager.get_message()

            if confirm_message is not None:
                self.confirm_label.config(
                    text=confirm_message,
                    fg="#cc8800"
                )
            elif not self.session_saved:
                self.confirm_label.config(
                    text="No action pending",
                    fg="#555555"
                )

            preview_frame = cv2.resize(frame, (320, 240))
            preview_frame = cv2.cvtColor(preview_frame, cv2.COLOR_BGR2RGB)

            image = Image.fromarray(preview_frame)
            self.camera_image = ImageTk.PhotoImage(image=image)

            self.camera_label.config(image=self.camera_image)

        self.root.after(15, self.update_loop)

    def on_close(self):
        self.camera.release()
        self.hand_detector.close()
        self.root.destroy()