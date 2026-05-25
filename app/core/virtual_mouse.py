"""
virtual_mouse.py
-----------------
Apple Assistive Touch-style floating circle that tracks your index fingertip
and performs a left-click when thumb and index finger pinch together.

Key design decisions
--------------------
- The circle follows ONLY the index fingertip (landmark 8).
- When a pinch is detected the cursor position is FROZEN so the circle
  doesn't chase the fingertip as it moves downward during the pinch action.
- A short cooldown prevents accidental double-clicks.
- The overlay window is always-on-top, click-through (WS_EX_TRANSPARENT on
  Windows, transparent input on other platforms via the Qt flag), and has no
  taskbar entry.

Dependencies already in requirements.txt:
    mediapipe, opencv-python, PyAutoGUI (add this one – see README).
"""

import math
import time
import threading

import cv2
import mediapipe as mp
import pyautogui

# ── tuneable constants ────────────────────────────────────────────────────────

# Pinch threshold: ratio of (thumb-tip ↔ index-tip distance) / palm size.
# Lower = fingers must be closer before a click fires.
PINCH_THRESHOLD = 0.18

# How long (seconds) to ignore further clicks after one fires.
CLICK_COOLDOWN = 0.6

# Smoothing factor for exponential moving average (0 = no smoothing, 1 = frozen).
SMOOTH_ALPHA = 0.35

# Number of consecutive frames a pinch must be held before the click fires.
PINCH_CONFIRM_FRAMES = 4

# ─────────────────────────────────────────────────────────────────────────────


class VirtualMouse:
    """
    Processes a single video frame and translates hand-landmark positions into
    mouse cursor movements / clicks.

    Usage
    -----
        vm = VirtualMouse(screen_w, screen_h, frame_w, frame_h)
        while True:
            frame = camera.read_frame()
            cursor_x, cursor_y, is_clicking = vm.process(frame)
            # move your overlay circle to (cursor_x, cursor_y)
    """

    # MediaPipe landmark indices used in this module
    _INDEX_TIP  = 8
    _THUMB_TIP  = 4
    _INDEX_MCP  = 5   # knuckle – used for palm-size reference
    _WRIST      = 0

    def __init__(self, screen_w: int, screen_h: int,
                 frame_w: int, frame_h: int,
                 move_mouse: bool = True):
        """
        Parameters
        ----------
        screen_w / screen_h : physical screen dimensions in pixels
        frame_w  / frame_h  : webcam frame dimensions
        move_mouse          : if True, also drives the OS mouse pointer so
                              real clicks land in the right place.
        """
        self.screen_w  = screen_w
        self.screen_h  = screen_h
        self.frame_w   = frame_w
        self.frame_h   = frame_h
        self.move_mouse = move_mouse

        # Smoothed cursor position
        self._cursor_x: float = screen_w / 2
        self._cursor_y: float = screen_h / 2

        # Frozen position held while a pinch is active
        self._frozen_x: float = screen_w / 2
        self._frozen_y: float = screen_h / 2

        # State machine
        self._pinch_frame_count: int  = 0
        self._is_pinching:       bool = False
        self._last_click_time:   float = 0.0

        # MediaPipe hands (single hand for mouse control)
        mp_hands = mp.solutions.hands
        self._hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.75,
        )

    # ── public API ────────────────────────────────────────────────────────────

    def process(self, frame) -> tuple[int, int, bool]:
        """
        Analyse one BGR frame from OpenCV.

        Returns
        -------
        (cursor_x, cursor_y, clicked_this_frame)
            cursor_x / cursor_y : where the overlay circle should sit (pixels)
            clicked_this_frame  : True only on the single frame the click fires
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)

        clicked_this_frame = False

        if not results.multi_hand_landmarks:
            # No hand detected – keep the last known position
            return int(self._frozen_x), int(self._frozen_y), False

        landmarks = results.multi_hand_landmarks[0].landmark

        # ── 1. Raw index-tip position mapped to screen space ─────────────────
        # We flip x so the cursor mirrors naturally (webcam is flipped).
        raw_x = (1.0 - landmarks[self._INDEX_TIP].x) * self.screen_w
        raw_y = landmarks[self._INDEX_TIP].y * self.screen_h

        # ── 2. Exponential smoothing ──────────────────────────────────────────
        self._cursor_x = self._cursor_x + SMOOTH_ALPHA * (raw_x - self._cursor_x)
        self._cursor_y = self._cursor_y + SMOOTH_ALPHA * (raw_y - self._cursor_y)

        # ── 3. Pinch detection ────────────────────────────────────────────────
        pinch_ratio = self._pinch_ratio(landmarks)
        is_pinch    = pinch_ratio < PINCH_THRESHOLD

        if is_pinch:
            self._pinch_frame_count += 1
        else:
            self._pinch_frame_count = 0
            self._is_pinching       = False

        # ── 4. Position freeze & click logic ─────────────────────────────────
        if self._is_pinching:
            # Already in a pinch – keep circle locked, don't re-click
            display_x, display_y = int(self._frozen_x), int(self._frozen_y)

        elif self._pinch_frame_count >= PINCH_CONFIRM_FRAMES:
            # New pinch confirmed this frame
            self._is_pinching = True

            # Freeze position to where the finger was BEFORE it moved down
            self._frozen_x = self._cursor_x
            self._frozen_y = self._cursor_y
            display_x, display_y = int(self._frozen_x), int(self._frozen_y)

            # Fire click (with cooldown guard)
            now = time.time()
            if now - self._last_click_time >= CLICK_COOLDOWN:
                self._last_click_time = now
                clicked_this_frame    = True
                self._fire_click(display_x, display_y)
        else:
            # Normal tracking – update frozen position to follow the finger
            self._frozen_x = self._cursor_x
            self._frozen_y = self._cursor_y
            display_x, display_y = int(self._frozen_x), int(self._frozen_y)

            # Move OS cursor even when not clicking
            if self.move_mouse:
                pyautogui.moveTo(display_x, display_y, _pause=False)

        return display_x, display_y, clicked_this_frame

    def get_pinch_ratio(self, frame) -> float:
        """
        Utility: return the current pinch ratio without side-effects.
        Useful for driving an animated progress ring on the overlay.
        Returns 1.0 when no hand is detected.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)
        if not results.multi_hand_landmarks:
            return 1.0
        return self._pinch_ratio(results.multi_hand_landmarks[0].landmark)

    def close(self):
        self._hands.close()

    # ── private helpers ───────────────────────────────────────────────────────

    def _pinch_ratio(self, landmarks) -> float:
        """
        Return (thumb-tip ↔ index-tip distance) / palm-size.
        A value below PINCH_THRESHOLD means the fingers are touching.
        """
        thumb  = landmarks[self._THUMB_TIP]
        index  = landmarks[self._INDEX_TIP]
        wrist  = landmarks[self._WRIST]
        middle_mcp = landmarks[9]   # centre of palm

        pinch_dist = math.hypot(
            (thumb.x - index.x) * self.frame_w,
            (thumb.y - index.y) * self.frame_h,
        )
        palm_size = math.hypot(
            (wrist.x - middle_mcp.x) * self.frame_w,
            (wrist.y - middle_mcp.y) * self.frame_h,
        ) or 1.0

        return pinch_dist / palm_size

    def _fire_click(self, x: int, y: int):
        """Move OS cursor to (x, y) then perform a left click in a thread."""
        def _click():
            pyautogui.moveTo(x, y, _pause=False)
            pyautogui.click()

        threading.Thread(target=_click, daemon=True).start()
