import tkinter as tk

from app.core.virtual_mouse import PINCH_THRESHOLD


CIRCLE_RADIUS = 34
CLICK_RADIUS = 26
RING_WIDTH = 4
CANVAS_SIZE = 120
WINDOW_ALPHA = 0.62


class AssistiveTouchCursor:
    def __init__(self, root):
        self.root = root
        self._center = CANVAS_SIZE // 2
        self._click_anim = 0.0
        self._pinch_ratio = 1.0
        self._visible = False
        self._last_root_x = 0
        self._last_root_y = 0
        self._restore_after_id = None
        self._animation_after_id = None

        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", WINDOW_ALPHA)
        self.window.withdraw()

        background = "systemTransparent"

        try:
            self.window.configure(bg=background)
            self.window.attributes("-transparent", True)
        except tk.TclError:
            background = root.cget("bg")
            self.window.configure(bg=background)

        try:
            self.canvas = tk.Canvas(
                self.window,
                width=CANVAS_SIZE,
                height=CANVAS_SIZE,
                highlightthickness=0,
                bd=0,
                bg=background
            )
        except tk.TclError:
            background = root.cget("bg")
            self.window.configure(bg=background)
            self.canvas = tk.Canvas(
                self.window,
                width=CANVAS_SIZE,
                height=CANVAS_SIZE,
                highlightthickness=0,
                bd=0,
                bg=background
            )
        self.canvas.pack()

        self._tick_animation()

    def update_cursor(self, root_x: int, root_y: int, pinch_ratio: float, clicked: bool):
        self._last_root_x = root_x
        self._last_root_y = root_y
        self._pinch_ratio = pinch_ratio

        if clicked:
            self._click_anim = 1.0

        if not self._visible:
            self.window.deiconify()
            self._visible = True

        self._position_window(root_x, root_y)
        self.window.lift()

        self._redraw(pinch_ratio)

    def hide(self):
        if self._restore_after_id is not None:
            self.root.after_cancel(self._restore_after_id)
            self._restore_after_id = None
        if self._visible:
            self.window.withdraw()
            self._visible = False

    def show(self):
        self._restore_after_id = None
        if not self._visible:
            self.window.deiconify()
            self._visible = True
            self.window.lift()
            self._position_window(self._last_root_x, self._last_root_y)

    def hide_temporarily(self, restore_delay_ms: int = 40):
        self.hide()
        if self._restore_after_id is not None:
            self.root.after_cancel(self._restore_after_id)
        self._restore_after_id = self.root.after(restore_delay_ms, self.show)

    def destroy(self):
        if self._restore_after_id is not None:
            self.root.after_cancel(self._restore_after_id)
        if self._animation_after_id is not None:
            self.root.after_cancel(self._animation_after_id)
        self.window.destroy()

    def _tick_animation(self):
        if self._click_anim > 0:
            self._click_anim = max(0.0, self._click_anim - 0.08)
            if self._visible:
                self._redraw(self._pinch_ratio)
        self._animation_after_id = self.root.after(16, self._tick_animation)

    def _position_window(self, root_x: int, root_y: int):
        app_left = self.root.winfo_rootx()
        app_top = self.root.winfo_rooty()
        app_right = app_left + max(1, self.root.winfo_width())
        app_bottom = app_top + max(1, self.root.winfo_height())

        screen_x = app_left + root_x - self._center
        screen_y = app_top + root_y - self._center

        clamped_x = min(max(screen_x, app_left), max(app_left, app_right - CANVAS_SIZE))
        clamped_y = min(max(screen_y, app_top), max(app_top, app_bottom - CANVAS_SIZE))

        self.window.geometry(
            f"{CANVAS_SIZE}x{CANVAS_SIZE}+{clamped_x}+{clamped_y}"
        )

    def _redraw(self, pinch_ratio: float = 1.0):
        self.canvas.delete("all")

        fill = max(
            0.0,
            min(1.0, 1.0 - (pinch_ratio - PINCH_THRESHOLD) / (1.0 - PINCH_THRESHOLD))
        )

        ring_radius = CIRCLE_RADIUS + RING_WIDTH
        ring_box = (
            self._center - ring_radius,
            self._center - ring_radius,
            self._center + ring_radius,
            self._center + ring_radius
        )

        self.canvas.create_oval(
            *ring_box,
            outline="#2A2A2A",
            width=RING_WIDTH
        )

        if fill > 0.01:
            self.canvas.create_arc(
                *ring_box,
                start=90,
                extent=-fill * 359.9,
                style="arc",
                outline="#5FD891",
                width=RING_WIDTH
            )

        radius = int(CIRCLE_RADIUS - (CIRCLE_RADIUS - CLICK_RADIUS) * self._click_anim)
        circle_box = (
            self._center - radius,
            self._center - radius,
            self._center + radius,
            self._center + radius
        )

        self.canvas.create_oval(
            *circle_box,
            fill="#E8F1FF",
            outline="#7BAEFF",
            width=2
        )

        inner_radius = max(12, radius - 10)
        inner_box = (
            self._center - inner_radius,
            self._center - inner_radius,
            self._center + inner_radius,
            self._center + inner_radius
        )
        self.canvas.create_oval(
            *inner_box,
            fill="#FDFEFF",
            outline=""
        )

        if self._click_anim > 0.01:
            ripple_radius = int(CIRCLE_RADIUS + self._click_anim * CIRCLE_RADIUS * 1.5)
            alpha_strength = int(120 * self._click_anim)
            ripple_color = f"#{80:02x}{160:02x}{255:02x}"
            self.canvas.create_oval(
                self._center - ripple_radius,
                self._center - ripple_radius,
                self._center + ripple_radius,
                self._center + ripple_radius,
                outline=ripple_color,
                width=max(1, alpha_strength // 40)
            )
