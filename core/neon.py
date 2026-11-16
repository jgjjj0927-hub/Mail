PALETTE = {
    "bg":        "#0a0a12",
    "bg_soft":   "#10101c",
    "panel":     "#151526",
    "border":    "#2a2a4a",
    "text":      "#e6e6ff",
    "muted":     "#7a7aa8",
    "neon_pink": "#ff2bd6",
    "neon_cyan": "#00e5ff",
    "neon_lime": "#9dff00",
    "neon_purple": "#a855ff",
    "danger":    "#ff3b6b",
    "ok":        "#00ffa3",
}

FONT_MAIN = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI Semibold", 16)
FONT_MONO = ("Consolas", 10)


def glow_button_style(widget, base_color: str):
    widget.configure(
        bg=base_color, fg="#0a0a12", activebackground=base_color,
        activeforeground="#0a0a12", relief="flat", bd=0,
        highlightthickness=2, highlightbackground=base_color,
        font=("Segoe UI Semibold", 10), cursor="hand2",
    )
