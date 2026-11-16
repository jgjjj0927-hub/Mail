import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys, os, threading, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import accounts, mailer, templates, subscriptions, crypto
from core.neon import PALETTE, FONT_MAIN, FONT_TITLE, FONT_MONO, glow_button_style
import config


class StampGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stamp — Neon Edition")
        self.geometry("840x680")
        self.configure(bg=PALETTE["bg"])
        self._current_user = None
        self._build()

    # ---------- helpers ----------
    def _neon_entry(self, parent, show=None):
        return tk.Entry(
            parent, bg=PALETTE["bg_soft"], fg=PALETTE["text"],
            insertbackground=PALETTE["neon_cyan"], relief="flat",
            highlightthickness=1, highlightbackground=PALETTE["border"],
            highlightcolor=PALETTE["neon_cyan"], font=FONT_MAIN, show=show or ""
        )

    def _neon_text(self, parent, height=8):
        return tk.Text(
            parent, height=height, bg=PALETTE["bg_soft"], fg=PALETTE["text"],
            insertbackground=PALETTE["neon_cyan"], relief="flat",
            highlightthickness=1, highlightbackground=PALETTE["border"],
            highlightcolor=PALETTE["neon_cyan"], font=FONT_MONO,
            padx=8, pady=8, wrap="word"
        )

    def _neon_label(self, parent, text, color=None, font=None):
        return tk.Label(
            parent, text=text, bg=PALETTE["bg"],
            fg=color or PALETTE["text"], font=font or FONT_MAIN
        )

    # ---------- screens ----------
    def _build(self):
        self._clear()
        if not self._current_user:
            self._screen_login()
        elif not subscriptions.has_active_sub(self._current_user):
            self._screen_sub_gate()
        else:
            self._screen_main()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    # ---------- login ----------
    def _screen_login(self):
        frame = tk.Frame(self, bg=PALETTE["bg"])
        frame.pack(expand=True)

        tk.Label(frame, text="STAMP", bg=PALETTE["bg"],
                 fg=PALETTE["neon_pink"], font=("Segoe UI Black", 32)).pack(pady=(0, 4))
        tk.Label(frame, text="neon broadcast engine", bg=PALETTE["bg"],
                 fg=PALETTE["muted"], font=("Segoe UI", 10)).pack(pady=(0, 24))

        self._neon_label(frame, "Telegram ID:").pack(anchor="w")
        e_uid = self._neon_entry(frame)
        e_uid.pack(fill="x", pady=(4, 12), ipady=6)

        btn = tk.Button(frame, text="ВОЙТИ",
                        command=lambda: self._do_login(e_uid.get().strip()))
        glow_button_style(btn, PALETTE["neon_cyan"])
        btn.pack(fill="x", ipady=8, pady=(8, 0))

        self._neon_label(frame, "Ключ активации (если нет подписки):",
                         color=PALETTE["muted"]).pack(anchor="w", pady=(20, 4))
        e_key = self._neon_entry(frame)
        e_key.pack(fill="x", ipady=6)

        btn2 = tk.Button(frame, text="АКТИВИРОВАТЬ КЛЮЧ",
                         command=lambda: self._do_activate(e_uid.get().strip(), e_key.get().strip()))
        glow_button_style(btn2, PALETTE["neon_lime"])
        btn2.pack(fill="x", ipady=8, pady=(8, 0))

    def _do_login(self, uid_str: str):
        try:
            uid = int(uid_str)
        except ValueError:
            messagebox.showerror("Stamp", "ID должен быть числом")
            return
        self._current_user = uid
        self._build()

    def _do_activate(self, uid_str: str, key: str):
        try:
            uid = int(uid_str)
        except ValueError:
            messagebox.showerror("Stamp", "Сначала введи корректный ID")
            return
        if not key:
            messagebox.showerror("Stamp", "Введи ключ")
            return
        try:
            info = subscriptions.activate_key(uid, key)
        except ValueError as e:
            messagebox.showerror("Stamp", str(e))
            return
        self._current_user = uid
        until = "навсегда" if info["until"] is None else time.strftime(
            "%Y-%m-%d %H:%M", time.localtime(info["until"]))
        messagebox.showinfo("Stamp", f"Ключ активирован. До: {until}")
        self._build()

    # ---------- subscription gate ----------
    def _screen_sub_gate(self):
        frame = tk.Frame(self, bg=PALETTE["bg"])
        frame.pack(expand=True)

        tk.Label(frame, text="💎", bg=PALETTE["bg"],
                 fg=PALETTE["neon_purple"], font=("Segoe UI Emoji", 48)).pack()
        tk.Label(frame, text="Подписка не активна", bg=PALETTE["bg"],
                 fg=PALETTE["neon_pink"], font=FONT_TITLE).pack(pady=(8, 4))
        tk.Label(frame, text="Купи подписку в ТГ-канале и активируй ключ.",
                 bg=PALETTE["bg"], fg=PALETTE["muted"], font=FONT_MAIN).pack(pady=(0, 20))

        btn = tk.Button(frame, text="ВВЕСТИ КЛЮЧ", command=self._screen_login)
        glow_button_style(btn, PALETTE["neon_lime"])
        btn.pack(ipady=8, ipadx=20)

    # ---------- main screen ----------
    def _screen_main(self):
        header = tk.Frame(self, bg=PALETTE["bg"])
        header.pack(fill="x", padx=20, pady=(16, 8))

        tk.Label(header, text="STAMP", bg=PALETTE["bg"],
                 fg=PALETTE["neon_pink"], font=("Segoe UI Black", 20)).pack(side="left")
        tk.Label(header, text=f"  id: {self._current_user}", bg=PALETTE["bg"],
                 fg=PALETTE["muted"], font=FONT_MAIN).pack(side="left", padx=12)

        info = subscriptions.get_sub_info(self._current_user) or {}
        until = "навсегда" if info.get("until") is None else time.strftime(
            "%Y-%m-%d %H:%M", time.localtime(info.get("until", 0)))
        tk.Label(header, text=f"до: {until}", bg=PALETTE["bg"],
                 fg=PALETTE["neon_cyan"], font=FONT_MAIN).pack(side="right")

        body = tk.Frame(self, bg=PALETTE["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=8)

        self._neon_label(body, "Почта (from):").pack(anchor="w")
        self.email_var = tk.StringVar()
        e1 = self._neon_entry(body)
        e1.config(textvariable=self.email_var)
        e1.pack(fill="x", ipady=6, pady=(2, 8))

        self._neon_label(body, "Код приложения:").pack(anchor="w")
        self.pass_var = tk.StringVar()
        e2 = self._neon_entry(body, show="*")
        e2.config(textvariable=self.pass_var)
        e2.pack(fill="x", ipady=6, pady=(2, 8))

        self._neon_label(body, "Тема:").pack(anchor="w")
        self.subj_var = tk.StringVar(value=templates.DEFAULT_SUBJECT)
        e3 = self._neon_entry(body)
        e3.config(textvariable=self.subj_var)
        e3.pack(fill="x", ipady=6, pady=(2, 8))

        self._neon_label(body, "Текст письма:").pack(anchor="w")
        self.body_txt = self._neon_text(body, height=8)
        self.body_txt.pack(fill="x", pady=(2, 8))

        self._neon_label(body, "Получатели (по одному в строке):").pack(anchor="w")
        self.rcpt_txt = self._neon_text(body, height=6)
        self.rcpt_txt.pack(fill="x", pady=(2, 8))

        row = tk.Frame(body, bg=PALETTE["bg"])
        row.pack(fill="x", pady=8)

        btn_load = tk.Button(row, text="📥 .TXT", command=self._load_txt)
        glow_button_style(btn_load, PALETTE["neon_purple"])
        btn_load.pack(side="left", ipady=6, ipadx=12)

        self.status_lbl = tk.Label(row, text="готов", bg=PALETTE["bg"],
                                   fg=PALETTE["muted"], font=FONT_MAIN)
        self.status_lbl.pack(side="left", padx=12)

        btn_send = tk.Button(row, text="🚀 ОТПРАВИТЬ", command=self._send)
        glow_button_style(btn_send, PALETTE["neon_pink"])
        btn_send.pack(side="right", ipady=6, ipadx=16)

    def _load_txt(self):
        p = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if not p:
            return
        with open(p, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if "@" in l]
        self.rcpt_txt.delete("1.0", "end")
        self.rcpt_txt.insert("1.0", "\n".join(lines))
        self.status_lbl.config(text=f"загружено: {len(lines)}", fg=PALETTE["neon_cyan"])

    def _send(self):
        if not subscriptions.has_active_sub(self._current_user):
            messagebox.showerror("Stamp", "Подписка не активна")
            return
        email = self.email_var.get().strip()
        pwd = self.pass_var.get().strip()
        subj = self.subj_var.get().strip()
        body = self.body_txt.get("1.0", "end").strip()
        rcpts = [x for x in self.rcpt_txt.get("1.0", "end").replace(",", " ").split() if "@" in x]

        if not (email and pwd and subj and body and rcpts):
            messagebox.showerror("Stamp", "Заполни все поля и добавь адреса")
            return

        self.status_lbl.config(text="отправка...", fg=PALETTE["neon_pink"])

        def worker():
            try:
                res = mailer.send_bulk(email, pwd, rcpts, subj, templates.render(body))
                self.after(0, lambda: self.status_lbl.config(
                    text=f"ок: {res['sent']} | ошибок: {res['failed']}",
                    fg=PALETTE["neon_lime"]))
            except Exception as e:
                self.after(0, lambda: self.status_lbl.config(
                    text=f"ошибка: {e}", fg=PALETTE["danger"]))

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    StampGUI().mainloop()
