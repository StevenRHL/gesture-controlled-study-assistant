"""
mouse_overlay.py
----------------
A frameless, always-on-top, transparent PyQt5/PySide6 window that renders the
Apple Assistive Touch-style floating circle.

The overlay imports VirtualMouse from app.core.virtual_mouse to process
webcam frames and translate hand gestures into cursor + click events.

Run this file directly to launch the overlay as a standalone feature:
    python -m app.ui.mouse_overlay

Or import MouseOverlay and embed it into the existing MainWindow if you prefer.
"""

import sys
import threading
import time

import cv2
from PyQt5.QtCore    import Qt, QTimer, QPoint, pyqtSignal, QObject
from PyQt5.QtGui     import QPainter, QColor, QBrush, QPen, QRadialGradient
from PyQt5.QtWidgets import QApplication, QWidget

from app.core.virtual_mouse import VirtualMouse, PINCH_THRESHOLD

# ── tuneable constants ────────────────────────────────────────────────────────
CIRCLE_RADIUS   = 34       # px – resting size of the assistive-touch circle
CLICK_RADIUS    = 26       # px – shrinks to this when a click fires
RING_WIDTH      = 4        # px – border ring thickness
CAMERA_INDEX    = 0
FPS_TARGET      = 30
# ─────────────────────────────────────────────────────────────────────────────


class _Bridge(QObject):
    """Tiny Qt signal bridge so the camera thread can update the UI safely."""
    frame_ready = pyqtSignal(int, int, float, bool)   # x, y, pinch_ratio, clicked


class MouseOverlayWidget(QWidget):
    """
    Transparent, click-through overlay window.
    Draws a semi-transparent circle that tracks the index finger.
    """

    def __init__(self):
        super().__init__()

        # Window flags: frameless, always on top, tool window (no taskbar entry)
        self.setWindowFlags(
            Qt.FramelessWindowHint     |
            Qt.WindowStaysOnTopHint    |
            Qt.Tool                    |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        # Cover the entire primary screen
        screen_geo = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geo)

        self._screen_w = screen_geo.width()
        self._screen_h = screen_geo.height()

        # Drawing state
        self._cx:          int   = self._screen_w  // 2
        self._cy:          int   = self._screen_h  // 2
        self._pinch_ratio: float = 1.0
        self._clicked:     bool  = False
        self._click_anim:  float = 0.0   # 0 → 1, drives the click ripple animation

        # Bridge + camera thread
        self._bridge = _Bridge()
        self._bridge.frame_ready.connect(self._on_frame)

        self._running = True
        self._thread  = threading.Thread(target=self._camera_loop, daemon=True)
        self._thread.start()

        # Animation timer (drives the ripple even between camera frames)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_animation)
        self._anim_timer.start(16)   # ~60 fps repaint

    # ── camera thread ─────────────────────────────────────────────────────────

    def _camera_loop(self):
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            print("[MouseOverlay] ERROR: cannot open camera.")
            return

        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        vm = VirtualMouse(
            screen_w=self._screen_w,
            screen_h=self._screen_h,
            frame_w=frame_w,
            frame_h=frame_h,
            move_mouse=True,
        )

        interval = 1.0 / FPS_TARGET

        while self._running:
            t0 = time.monotonic()

            ok, frame = cap.read()
            if not ok:
                continue

            cx, cy, clicked = vm.process(frame)

            # Re-compute pinch ratio for the progress ring
            # (reuse the same flipped frame VirtualMouse already processed)
            pinch_ratio = vm._pinch_ratio(
                vm._hands.process(
                    cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                ).multi_hand_landmarks[0].landmark
                if True else None   # guard handled inside VirtualMouse
            ) if False else self._safe_pinch(vm, frame)

            self._bridge.frame_ready.emit(cx, cy, pinch_ratio, clicked)

            elapsed = time.monotonic() - t0
            sleep_t = interval - elapsed
            if sleep_t > 0:
                time.sleep(sleep_t)

        vm.close()
        cap.release()

    @staticmethod
    def _safe_pinch(vm: VirtualMouse, frame) -> float:
        """Return pinch ratio without crashing if no hand is in frame."""
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = vm._hands.process(rgb)
            if results.multi_hand_landmarks:
                return vm._pinch_ratio(results.multi_hand_landmarks[0].landmark)
        except Exception:
            pass
        return 1.0

    # ── Qt slots ──────────────────────────────────────────────────────────────

    def _on_frame(self, cx: int, cy: int, pinch_ratio: float, clicked: bool):
        self._cx = cx
        self._cy = cy
        self._pinch_ratio = pinch_ratio
        if clicked:
            self._click_anim = 1.0   # start ripple
        self.update()

    def _tick_animation(self):
        if self._click_anim > 0:
            self._click_anim = max(0.0, self._click_anim - 0.06)
            self.update()

    # ── painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx, cy = self._cx, self._cy

        # --- pinch progress ring -----------------------------------------
        # Ring fills as the user closes their fingers toward the threshold.
        # pinch_ratio == 1.0 → open hand; 0.0 → fully closed.
        # We map: 1.0 → empty ring, <= PINCH_THRESHOLD → full ring.
        fill = max(0.0, min(1.0,
            1.0 - (self._pinch_ratio - PINCH_THRESHOLD) / (1.0 - PINCH_THRESHOLD)
        ))

        ring_radius = CIRCLE_RADIUS + RING_WIDTH // 2

        # Background ring (dark translucent)
        pen_bg = QPen(QColor(0, 0, 0, 60), RING_WIDTH)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawEllipse(
            cx - ring_radius, cy - ring_radius,
            ring_radius * 2,  ring_radius * 2
        )

        # Progress arc
        if fill > 0.01:
            pen_prog = QPen(QColor(80, 200, 120, 200), RING_WIDTH)
            pen_prog.setCapStyle(Qt.RoundCap)
            painter.setPen(pen_prog)
            span_angle = int(-fill * 360 * 16)   # Qt uses 1/16 degrees, CCW
            painter.drawArc(
                cx - ring_radius, cy - ring_radius,
                ring_radius * 2,  ring_radius * 2,
                90 * 16, span_angle
            )

        # --- main circle -------------------------------------------------
        # Shrinks slightly during a click animation.
        anim      = self._click_anim
        radius    = int(CIRCLE_RADIUS - (CIRCLE_RADIUS - CLICK_RADIUS) * anim)

        # Radial gradient: white centre fading to a blue-tinted edge
        gradient = QRadialGradient(cx, cy, radius)
        gradient.setColorAt(0.0, QColor(255, 255, 255, 210))
        gradient.setColorAt(0.6, QColor(180, 210, 255, 180))
        gradient.setColorAt(1.0, QColor(100, 160, 255, 120))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

        # --- click ripple ------------------------------------------------
        if anim > 0.01:
            ripple_r = int(CIRCLE_RADIUS + anim * CIRCLE_RADIUS * 1.5)
            alpha    = int(anim * 160)
            pen_rip  = QPen(QColor(80, 160, 255, alpha), 2)
            painter.setPen(pen_rip)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(cx - ripple_r, cy - ripple_r,
                                ripple_r * 2,  ripple_r * 2)

        painter.end()

    # ── cleanup ───────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._running = False
        self._thread.join(timeout=2)
        super().closeEvent(event)


# ── standalone entry point ────────────────────────────────────────────────────

def run_overlay():
    """Launch the virtual-mouse overlay as a standalone process."""
    import pyautogui
    pyautogui.FAILSAFE = False   # prevent corner-throw exception during testing

    app = QApplication(sys.argv)
    overlay = MouseOverlayWidget()
    overlay.show()

    print("[MouseOverlay] Running – pinch index + thumb to click. Close window to exit.")
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_overlay()
