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
from typing import Callable, Optional

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

# Start slowing the cursor before the click threshold is reached.
PRE_PINCH_SLOWDOWN_THRESHOLD = 0.34

# Minimum cursor movement scale while the fingers are nearly pinched.
PRE_PINCH_MIN_MOVEMENT_SCALE = 0.08

# Number of consecutive frames a pinch must be held before the click fires.
PINCH_CONFIRM_FRAMES = 2

SCROLL_STEP_PIXELS = 22
SCROLL_DELTA_UNITS = 120
CURSOR_GAIN_X = 1.9
CURSOR_GAIN_Y = 1.9

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
                 move_mouse: bool = True,
                 mirror_x: bool = True,
                 preferred_hand_label: Optional[str] = None,
                 fallback_to_any_hand: bool = True,
                 click_handler: Optional[Callable[[int, int], None]] = None):
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
        self.mirror_x = mirror_x
        self.preferred_hand_label = preferred_hand_label
        self.fallback_to_any_hand = fallback_to_any_hand
        self.click_handler = click_handler

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
        self.last_pinch_ratio:   float = 1.0
        self._scroll_anchor_y: Optional[float] = None

        # MediaPipe hands (single hand for mouse control)
        mp_hands = mp.solutions.hands
        self._hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2 if preferred_hand_label else 1,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.75,
        )

    # ── public API ────────────────────────────────────────────────────────────

    def process(self, frame) -> tuple[int, int, bool, int]:
        """
        Analyse one BGR frame from OpenCV.

        Returns
        -------
        (cursor_x, cursor_y, clicked_this_frame, scroll_delta)
            cursor_x / cursor_y : where the overlay circle should sit (pixels)
            clicked_this_frame  : True only on the single frame the click fires
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)

        clicked_this_frame = False
        scroll_delta = 0

        if not results.multi_hand_landmarks:
            # No hand detected – keep the last known position
            self.last_pinch_ratio = 1.0
            self._scroll_anchor_y = None
            return int(self._frozen_x), int(self._frozen_y), False, 0

        hand_index = self._select_hand_index(results)
        if hand_index is None:
            self.last_pinch_ratio = 1.0
            self._scroll_anchor_y = None
            return int(self._frozen_x), int(self._frozen_y), False, 0

        landmarks = results.multi_hand_landmarks[hand_index].landmark

        # ── 1. Pinch detection ────────────────────────────────────────────────
        pinch_ratio = self._pinch_ratio(landmarks)
        self.last_pinch_ratio = pinch_ratio
        is_pinch    = pinch_ratio < PINCH_THRESHOLD
        is_scroll_gesture = is_pinch and self._is_scroll_gesture(landmarks)

        # ── 2. Raw index-tip position mapped to screen space ─────────────────
        # We flip x so the cursor mirrors naturally (webcam is flipped).
        x_ratio = 1.0 - landmarks[self._INDEX_TIP].x if self.mirror_x else landmarks[self._INDEX_TIP].x
        x_ratio = self._apply_cursor_gain(x_ratio, CURSOR_GAIN_X)
        y_ratio = self._apply_cursor_gain(landmarks[self._INDEX_TIP].y, CURSOR_GAIN_Y)
        raw_x = x_ratio * self.screen_w
        raw_y = y_ratio * self.screen_h

        # ── 3. Exponential smoothing with pre-pinch slowdown ─────────────────
        movement_scale = self._movement_scale_for_pinch(pinch_ratio)
        effective_alpha = SMOOTH_ALPHA * movement_scale
        self._cursor_x = self._cursor_x + effective_alpha * (raw_x - self._cursor_x)
        self._cursor_y = self._cursor_y + effective_alpha * (raw_y - self._cursor_y)

        if is_scroll_gesture:
            self._pinch_frame_count = 0
            self._is_pinching = False
            display_x, display_y = int(self._cursor_x), int(self._cursor_y)
            self._frozen_x = self._cursor_x
            self._frozen_y = self._cursor_y
            scroll_delta = self._compute_scroll_delta(landmarks)

        elif is_pinch:
            self._pinch_frame_count += 1
            self._scroll_anchor_y = None
        else:
            self._pinch_frame_count = 0
            self._is_pinching       = False
            self._scroll_anchor_y = None

        # ── 4. Position freeze & click logic ─────────────────────────────────
        if is_scroll_gesture:
            if self.move_mouse:
                pyautogui.moveTo(display_x, display_y, _pause=False)

        elif self._is_pinching:
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

        return display_x, display_y, clicked_this_frame, scroll_delta

    def set_output_size(self, width: int, height: int):
        self.screen_w = max(1, width)
        self.screen_h = max(1, height)
        max_x = max(0, self.screen_w - 1)
        max_y = max(0, self.screen_h - 1)
        self._cursor_x = min(max(self._cursor_x, 0), max_x)
        self._cursor_y = min(max(self._cursor_y, 0), max_y)
        self._frozen_x = min(max(self._frozen_x, 0), max_x)
        self._frozen_y = min(max(self._frozen_y, 0), max_y)

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
        hand_index = self._select_hand_index(results)
        if hand_index is None:
            return 1.0
        return self._pinch_ratio(results.multi_hand_landmarks[hand_index].landmark)

    def close(self):
        self._hands.close()

    # ── private helpers ───────────────────────────────────────────────────────

    def _select_hand_index(self, results) -> Optional[int]:
        if not results.multi_hand_landmarks:
            return None

        if self.preferred_hand_label is None:
            return 0

        if results.multi_handedness:
            for index, handedness in enumerate(results.multi_handedness):
                label = handedness.classification[0].label
                if label == self.preferred_hand_label:
                    return index

        if self.fallback_to_any_hand:
            return 0

        return None

    def _movement_scale_for_pinch(self, pinch_ratio: float) -> float:
        if pinch_ratio >= PRE_PINCH_SLOWDOWN_THRESHOLD:
            return 1.0

        if pinch_ratio <= PINCH_THRESHOLD:
            return PRE_PINCH_MIN_MOVEMENT_SCALE

        range_size = PRE_PINCH_SLOWDOWN_THRESHOLD - PINCH_THRESHOLD
        closeness = (PRE_PINCH_SLOWDOWN_THRESHOLD - pinch_ratio) / range_size
        slowdown = 1.0 - closeness * (1.0 - PRE_PINCH_MIN_MOVEMENT_SCALE)
        return max(PRE_PINCH_MIN_MOVEMENT_SCALE, min(1.0, slowdown))

    def _apply_cursor_gain(self, value: float, gain: float) -> float:
        centered_value = (value - 0.5) * gain + 0.5
        return max(0.0, min(1.0, centered_value))

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

    def _is_scroll_gesture(self, landmarks) -> bool:
        return all(
            landmarks[tip].y < landmarks[pip].y
            for tip, pip in ((12, 10), (16, 14), (20, 18))
        )

    def _compute_scroll_delta(self, landmarks) -> int:
        average_y = (
            landmarks[12].y + landmarks[16].y + landmarks[20].y
        ) / 3 * self.screen_h

        if self._scroll_anchor_y is None:
            self._scroll_anchor_y = average_y
            return 0

        movement = average_y - self._scroll_anchor_y

        if abs(movement) < SCROLL_STEP_PIXELS:
            return 0

        steps = int(movement / SCROLL_STEP_PIXELS)
        self._scroll_anchor_y += steps * SCROLL_STEP_PIXELS
        return -steps * SCROLL_DELTA_UNITS

    def _fire_click(self, x: int, y: int):
        """Move OS cursor to (x, y) then perform a left click in a thread."""
        if self.click_handler is not None:
            self.click_handler(x, y)
            return

        def _click():
            pyautogui.moveTo(x, y, _pause=False)
            pyautogui.click()

        threading.Thread(target=_click, daemon=True).start()
