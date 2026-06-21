"""Clippy-style floating widget for Hero."""

import math
import queue
import tkinter as tk


class HeroWidget:
    SIZE = 200
    BG = "systemTransparent"
    BODY_COLOR = "#4A90D9"
    BODY_OUTLINE = "#2C5F8A"
    EYE_WHITE = "#FFFFFF"
    PUPIL_COLOR = "#1A1A2E"
    RING_COLOR = "#7AB8F5"
    POLL_MS = 30

    def __init__(self, state_queue: queue.Queue) -> None:
        self._queue = state_queue
        self._state = "idle"
        self._amplitude = 0.0
        self._tick = 0
        self._goodbye_scale = 1.0
        self._rings: list[tuple[float, float]] = []

        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.wm_attributes("-transparent", True)
        self._root.config(bg=self.BG)

        self._canvas = tk.Canvas(
            self._root,
            width=self.SIZE,
            height=self.SIZE,
            bg=self.BG,
            highlightthickness=0,
        )
        self._canvas.pack()

        # Position bottom-right of screen
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        self._root.geometry(f"+{sw - self.SIZE - 40}+{sh - self.SIZE - 80}")

        # Dragging support
        self._drag_x = 0
        self._drag_y = 0
        self._canvas.bind("<Button-1>", self._start_drag)
        self._canvas.bind("<B1-Motion>", self._on_drag)

        self._root.after(self.POLL_MS, self._update)

    def _start_drag(self, event: tk.Event) -> None:
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event: tk.Event) -> None:
        x = self._root.winfo_x() + event.x - self._drag_x
        y = self._root.winfo_y() + event.y - self._drag_y
        self._root.geometry(f"+{x}+{y}")

    def _update(self) -> None:
        # Poll state queue
        try:
            while True:
                msg = self._queue.get_nowait()
                if isinstance(msg, tuple) and msg[0] == "amplitude":
                    self._amplitude = msg[1]
                else:
                    self._state = msg
                    if msg == "idle":
                        self._amplitude = 0.0
                        self._rings.clear()
        except queue.Empty:
            pass

        self._tick += 1
        self._canvas.delete("all")

        if self._state == "goodbye":
            self._draw_goodbye()
        else:
            self._draw_character()

        self._root.after(self.POLL_MS, self._update)

    def _draw_character(self) -> None:
        cx, cy = self.SIZE / 2, self.SIZE / 2
        base_r = 60

        # Breathing: gentle scale pulse in idle
        if self._state == "idle":
            breath = 1.0 + 0.03 * math.sin(self._tick * 0.05)
        elif self._state == "listening":
            breath = 1.0 + 0.02 * math.sin(self._tick * 0.15)
        else:
            breath = 1.0

        # Speaking: scale body with amplitude
        amp_scale = 1.0 + self._amplitude * 0.3
        r = base_r * breath * amp_scale

        # Radiating rings when speaking
        if self._state == "speaking" and self._amplitude > 0.05:
            if self._tick % 6 == 0:
                self._rings.append((r + 5, 0.8))

        new_rings = []
        for ring_r, ring_alpha in self._rings:
            ring_r += 1.5
            ring_alpha -= 0.02
            if ring_alpha > 0 and ring_r < self.SIZE / 2:
                # Approximate alpha by blending with a lighter color
                blend = int(0x4A + (0xFF - 0x4A) * (1 - ring_alpha))
                blend_g = int(0x90 + (0xFF - 0x90) * (1 - ring_alpha))
                blend_b = int(0xD9 + (0xFF - 0xD9) * (1 - ring_alpha))
                color = f"#{blend:02x}{blend_g:02x}{blend_b:02x}"
                self._canvas.create_oval(
                    cx - ring_r,
                    cy - ring_r,
                    cx + ring_r,
                    cy + ring_r,
                    outline=color,
                    width=2,
                )
                new_rings.append((ring_r, ring_alpha))
        self._rings = new_rings

        # Body circle
        self._canvas.create_oval(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            fill=self.BODY_COLOR,
            outline=self.BODY_OUTLINE,
            width=3,
        )

        # Eyes
        eye_w = 10 * breath
        eye_h = 10 * breath
        if self._state == "listening":
            eye_h = 13 * breath  # Wider eyes when listening

        for ex in [-18, 18]:
            # White
            self._canvas.create_oval(
                cx + ex - eye_w,
                cy - 12 - eye_h,
                cx + ex + eye_w,
                cy - 12 + eye_h,
                fill=self.EYE_WHITE,
                outline="",
            )
            # Pupil
            pr = 5 * breath
            self._canvas.create_oval(
                cx + ex - pr,
                cy - 12 - pr,
                cx + ex + pr,
                cy - 12 + pr,
                fill=self.PUPIL_COLOR,
                outline="",
            )

        # Mouth - small smile
        mouth_w = 12 * breath
        self._canvas.create_arc(
            cx - mouth_w,
            cy + 5,
            cx + mouth_w,
            cy + 25,
            start=200,
            extent=140,
            style="arc",
            outline=self.PUPIL_COLOR,
            width=2,
        )

    def _draw_goodbye(self) -> None:
        self._goodbye_scale *= 0.92
        if self._goodbye_scale < 0.01:
            self._root.quit()
            return

        cx, cy = self.SIZE / 2, self.SIZE / 2
        r = 60 * self._goodbye_scale

        # Fading body
        alpha = self._goodbye_scale
        blend = int(0x4A * alpha + 0xFF * (1 - alpha))
        blend_g = int(0x90 * alpha + 0xFF * (1 - alpha))
        blend_b = int(0xD9 * alpha + 0xFF * (1 - alpha))
        color = f"#{min(255, blend):02x}{min(255, blend_g):02x}{min(255, blend_b):02x}"

        self._canvas.create_oval(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            fill=color,
            outline="",
            width=0,
        )

    def run(self) -> None:
        self._root.mainloop()

    def destroy(self) -> None:
        try:
            self._root.quit()
        except Exception:
            pass
