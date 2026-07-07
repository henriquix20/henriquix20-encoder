# ═══════════════════════════════════════════════════════
#  Henriquix20 Encoder — gui.py
# ═══════════════════════════════════════════════════════

import os
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image

from config import APP_NAME, APP_VERSION, OUTPUT_SUFFIX
from updater import check_for_update
from encoder import get_output_path, copy_file
from patcher import patch_file, get_fps

C_BG        = "#0a0a0a"
C_CARD      = "#141414"
C_CARD2     = "#1a1a1a"
C_CARD3     = "#111111"
C_BORDER    = "#252525"
C_BORDER_LT = "#303030"
C_GREEN     = "#7ED321"
C_GREEN_HV  = "#6ab81a"
C_GREEN_DIS = "#1a2a0a"
C_GREEN_DIM = "#3a5a10"
C_WHITE     = "#f0f0f0"
C_TEXT_MID  = "#888888"
C_TEXT_DIM  = "#404040"
C_RED       = "#e53935"
C_YELLOW    = "#ffd54f"
C_BLUE      = "#64b5f6"
F           = "Segoe UI"


class HX20EncoderApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.input_path  = ctk.StringVar()
        self.output_dir  = ctk.StringVar(value="same")
        self.fps_display = ctk.StringVar(value="—")
        self.processing  = False
        self.file_loaded = False

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self._load_logo()
        self._build_ui()
        self.after(2000, self._check_update)

    def _check_update(self):
        """Check GitHub for newer version in background."""
        def on_result(version, url):
            if not version:
                return
            self.after(0, lambda: self._show_update_banner(version, url))
        check_for_update(on_result)

    def _show_update_banner(self, version, url):
        """Show a non-intrusive update banner at the top of the app."""
        import webbrowser
        banner = ctk.CTkFrame(self, fg_color="#1a2a0a", corner_radius=0)
        banner.place(relx=0, rely=0, relwidth=1)

        inner = ctk.CTkFrame(banner, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(
            inner,
            text=f"⚡  New version {version} available!",
            font=ctk.CTkFont(F, 11, "bold"),
            text_color=C_GREEN,
        ).pack(side="left")

        ctk.CTkButton(
            inner,
            text="Download",
            font=ctk.CTkFont(F, 11, "bold"),
            fg_color=C_GREEN, hover_color=C_GREEN_HV,
            text_color=C_BG,
            width=90, height=26, corner_radius=6,
            command=lambda: webbrowser.open(url),
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            inner,
            text="✕",
            font=ctk.CTkFont(F, 11),
            fg_color="transparent",
            hover_color=C_CARD2,
            text_color=C_TEXT_DIM,
            width=26, height=26, corner_radius=6,
            command=banner.destroy,
        ).pack(side="right")

    def _load_logo(self):
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            pil_img   = Image.open(logo_path).convert("RGBA")
            self.logo_img = ctk.CTkImage(pil_img, size=(94, 47))
        except Exception:
            self.logo_img = None

    # ──────────────────────────────────────────────────
    #  BUILD UI
    # ──────────────────────────────────────────────────

    def _build_ui(self):
        self.title(f"{APP_NAME}  v{APP_VERSION}")
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "logo.ico")
            if not os.path.isfile(icon_path):
                # PyInstaller bundled path
                import sys
                base = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
                icon_path = os.path.join(base, "logo.ico")
            if os.path.isfile(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass
        self.geometry("760x640")
        self.resizable(False, False)
        self.configure(fg_color=C_BG)
        PAD = 20

        # ── HEADER ──────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=12)
        hdr.pack(fill="x", padx=PAD, pady=(PAD, 0))
        hdr_inner = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_inner.pack(fill="x", padx=18, pady=12)

        if self.logo_img:
            ctk.CTkLabel(hdr_inner, image=self.logo_img, text="",
                         fg_color="transparent").pack(side="left")
        else:
            fb = ctk.CTkFrame(hdr_inner, fg_color=C_GREEN, width=48, height=48, corner_radius=10)
            fb.pack(side="left"); fb.pack_propagate(False)
            ctk.CTkLabel(fb, text="H", font=ctk.CTkFont(F, 22, "bold"),
                         text_color=C_BG).place(relx=.5, rely=.5, anchor="center")

        txt = ctk.CTkFrame(hdr_inner, fg_color="transparent")
        txt.pack(side="left", padx=(24, 0))
        ctk.CTkLabel(txt, text=APP_NAME,
                     font=ctk.CTkFont(F, 20, "bold"),
                     text_color=C_WHITE, anchor="w").pack(anchor="w")
        ctk.CTkLabel(txt, text="TikTok video encoder — optimized for quality",
                     font=ctk.CTkFont(F, 11),
                     text_color=C_TEXT_MID, anchor="w").pack(anchor="w")

        right = ctk.CTkFrame(hdr_inner, fg_color="transparent")
        right.pack(side="right")
        self.ffmpeg_dot = ctk.CTkLabel(right, text="●",
                                        font=ctk.CTkFont(size=14),
                                        text_color=C_TEXT_DIM)
        self.ffmpeg_dot.pack(side="right", padx=(5, 0))
        self.ffmpeg_lbl = ctk.CTkLabel(right, text="Ready",
                                        font=ctk.CTkFont(F, 11),
                                        text_color=C_GREEN)
        self.ffmpeg_lbl.pack(side="right")
        self.ffmpeg_dot.configure(text_color=C_GREEN)

        # ── DROP ZONE ───────────────────────────────────
        self.drop_frame = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=12,
                                        border_width=1, border_color=C_BORDER)
        self.drop_frame.pack(fill="x", padx=PAD, pady=(10, 0))

        icon_lbl = ctk.CTkLabel(self.drop_frame, text="↑",
                                 font=ctk.CTkFont(F, 26, "bold"),
                                 text_color=C_TEXT_DIM)
        icon_lbl.pack(pady=(20, 0))

        self.drop_label = ctk.CTkLabel(self.drop_frame,
                                        text="Drop your video here  or  click to browse",
                                        font=ctk.CTkFont(F, 13),
                                        text_color=C_TEXT_DIM, cursor="hand2")
        self.drop_label.pack(pady=(4, 20))

        for w in [self.drop_frame, self.drop_label, icon_lbl]:
            w.drop_target_register(DND_FILES)
            w.dnd_bind("<<Drop>>", self._on_drop)
            w.bind("<Button-1>", lambda e: self._select_file())
            w.bind("<Enter>", lambda e: self.drop_frame.configure(fg_color=C_CARD2))
            w.bind("<Leave>", lambda e: self.drop_frame.configure(fg_color=C_CARD))

        # File meta row
        meta = ctk.CTkFrame(self, fg_color="transparent")
        meta.pack(fill="x", padx=PAD, pady=(5, 0))
        self.file_name_lbl = ctk.CTkLabel(meta, text="No file selected",
                                           font=ctk.CTkFont(F, 11),
                                           text_color=C_TEXT_DIM, anchor="w")
        self.file_name_lbl.pack(side="left")

        # FPS pill
        fps_pill = ctk.CTkFrame(meta, fg_color=C_CARD2, corner_radius=6)
        fps_pill.pack(side="right")
        ctk.CTkLabel(fps_pill, text="FPS",
                     font=ctk.CTkFont(F, 9, "bold"),
                     text_color=C_TEXT_DIM).pack(side="left", padx=(8, 3), pady=4)
        self.fps_lbl = ctk.CTkLabel(fps_pill, textvariable=self.fps_display,
                                     font=ctk.CTkFont(F, 11, "bold"),
                                     text_color=C_GREEN)
        self.fps_lbl.pack(side="left", padx=(0, 8), pady=4)

        self.file_size_lbl = ctk.CTkLabel(meta, text="",
                                           font=ctk.CTkFont(F, 11),
                                           text_color=C_TEXT_DIM, anchor="e")
        self.file_size_lbl.pack(side="right", padx=(0, 10))

        # ── OUTPUT DESTINATION ──────────────────────────
        out_frame = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=12)
        out_frame.pack(fill="x", padx=PAD, pady=(10, 0))
        out_inner = ctk.CTkFrame(out_frame, fg_color="transparent")
        out_inner.pack(fill="x", padx=20, pady=12)

        ctk.CTkLabel(out_inner, text="OUTPUT",
                     font=ctk.CTkFont(F, 9, "bold"),
                     text_color=C_TEXT_DIM, anchor="w").pack(anchor="w", pady=(0, 8))

        out_row = ctk.CTkFrame(out_inner, fg_color="transparent")
        out_row.pack(fill="x")

        self.out_same_btn = ctk.CTkButton(
            out_row, text="Same folder as video",
            font=ctk.CTkFont(F, 12, "bold"),
            width=180, height=34, corner_radius=8,
            fg_color=C_GREEN, hover_color=C_GREEN_HV, text_color=C_BG,
            command=self._set_output_same,
        )
        self.out_same_btn.pack(side="left")

        self.out_custom_btn = ctk.CTkButton(
            out_row, text="Choose folder",
            font=ctk.CTkFont(F, 12, "bold"),
            width=140, height=34, corner_radius=8,
            fg_color=C_CARD2, hover_color=C_BORDER_LT,
            text_color=C_TEXT_MID,
            border_width=1, border_color=C_BORDER,
            command=self._set_output_custom,
        )
        self.out_custom_btn.pack(side="left", padx=(8, 0))

        self.out_path_lbl = ctk.CTkLabel(out_row,
                                          text="→  same folder as input",
                                          font=ctk.CTkFont(F, 11, slant="italic"),
                                          text_color=C_TEXT_DIM, anchor="w")
        self.out_path_lbl.pack(side="left", padx=(14, 0))

        # ── PROCESS BUTTON ──────────────────────────────
        self.process_btn = ctk.CTkButton(
            self,
            text="⚡   PROCESS VIDEO",
            font=ctk.CTkFont(F, 14, "bold"),
            fg_color=C_GREEN_DIS,
            hover_color=C_GREEN_HV,
            text_color=C_GREEN_DIM,
            height=50, corner_radius=10,
            state="disabled",
            command=self._start_processing,
        )
        self.process_btn.pack(fill="x", padx=PAD, pady=(12, 0))

        # ── PROGRESS ────────────────────────────────────
        prog_frame = ctk.CTkFrame(self, fg_color="transparent")
        prog_frame.pack(fill="x", padx=PAD, pady=(10, 0))

        self.progress = ctk.CTkProgressBar(prog_frame, height=5, corner_radius=3,
                                            fg_color=C_CARD2,
                                            progress_color=C_GREEN)
        self.progress.set(0)
        self.progress.pack(fill="x")

        prog_meta = ctk.CTkFrame(prog_frame, fg_color="transparent")
        prog_meta.pack(fill="x", pady=(4, 0))
        self.progress_label = ctk.CTkLabel(prog_meta, text="",
                                            font=ctk.CTkFont(F, 10),
                                            text_color=C_TEXT_DIM, anchor="w")
        self.progress_label.pack(side="left")
        self.progress_pct = ctk.CTkLabel(prog_meta, text="",
                                          font=ctk.CTkFont(F, 10, "bold"),
                                          text_color=C_TEXT_MID, anchor="e")
        self.progress_pct.pack(side="right")

        # ── LOG ─────────────────────────────────────────
        self.log_box = ctk.CTkTextbox(
            self,
            fg_color=C_CARD3,
            text_color="#555555",
            font=ctk.CTkFont("Consolas", 11),
            corner_radius=12,
            border_width=0,
            wrap="word",
        )
        self.log_box.pack(fill="both", expand=True, padx=PAD, pady=(8, PAD))
        self.log_box.configure(state="disabled")

    # ──────────────────────────────────────────────────
    #  OUTPUT HANDLERS
    # ──────────────────────────────────────────────────

    def _set_output_same(self):
        self.output_dir.set("same")
        self.out_same_btn.configure(fg_color=C_GREEN, text_color=C_BG)
        self.out_custom_btn.configure(fg_color=C_CARD2, text_color=C_TEXT_MID)
        self.out_path_lbl.configure(text="→  same folder as input")

    def _set_output_custom(self):
        path = filedialog.askdirectory(title="Choose output folder")
        if not path:
            return
        self.output_dir.set(path)
        self.out_same_btn.configure(fg_color=C_CARD2, text_color=C_TEXT_MID)
        self.out_custom_btn.configure(fg_color=C_GREEN, text_color=C_BG)
        short = path if len(path) < 42 else "..." + path[-38:]
        self.out_path_lbl.configure(text=f"→  {short}")

    # ──────────────────────────────────────────────────
    #  FILE HANDLERS
    # ──────────────────────────────────────────────────

    def _on_drop(self, event):
        path = event.data.strip().strip("{}")
        self._set_input(path)

    def _select_file(self):
        path = filedialog.askopenfilename(
            title="Select video",
            filetypes=[("Video files", "*.mp4 *.mov *.avi *.mkv *.webm"),
                       ("All files", "*.*")]
        )
        if path:
            self._set_input(path)

    def _set_input(self, path):
        if not os.path.isfile(path):
            messagebox.showerror("Error", f"File not found:\n{path}")
            return

        self.input_path.set(path)
        self.file_loaded = True
        name    = os.path.basename(path)
        size_mb = os.path.getsize(path) / (1024 * 1024)

        # Detect FPS
        fps = get_fps(path)
        self.fps_display.set(f"{fps:.0f}" if fps else "?")

        self.drop_frame.configure(border_color=C_GREEN)
        self.drop_label.configure(
            text=f"✓  {name}     Click to change",
            text_color=C_GREEN,
        )
        self.file_name_lbl.configure(text=name, text_color=C_TEXT_MID)
        self.file_size_lbl.configure(text=f"{size_mb:.1f} MB")

        self.process_btn.configure(
            state="normal", fg_color=C_GREEN, text_color=C_BG)

        self._log_clear()
        self._log(f"Loaded:  {name}")
        self._log(f"Size:    {size_mb:.1f} MB")
        self._log(f"FPS:     {fps:.0f}" if fps else "FPS:     unknown")
        self._set_progress(0)
        self._set_progress_label("")
        self._set_progress_pct("")

    # ──────────────────────────────────────────────────
    #  PROCESSING
    # ──────────────────────────────────────────────────

    def _start_processing(self):
        if self.processing or not self.file_loaded:
            return
        path = self.input_path.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Please select a video file first.")
            return

        self.processing = True
        self.process_btn.configure(state="disabled", fg_color=C_CARD2,
                                    text_color=C_TEXT_DIM, text="Processing...")
        self.progress.configure(progress_color=C_GREEN)
        self._set_progress(0)
        self._set_progress_label("Starting...")
        self._set_progress_pct("0%")
        self._log("─" * 52)

        threading.Thread(
            target=self._process_thread,
            args=(path, self.output_dir.get()),
            daemon=True,
        ).start()

    def _process_thread(self, input_path, out_dir):
        output_path = get_output_path(input_path, out_dir)
        try:
            # Step 1: Copy
            self._set_progress_label("Copying file...")
            ok = copy_file(
                input_path, output_path,
                log_cb=self._log,
                progress_cb=self._on_progress,
            )
            if not ok:
                self._log("Copy failed.")
                self._finish(success=False, output_path=None)
                return

            # Step 2: Patch
            self._set_progress(0.90)
            self._set_progress_label("Applying 10x patch...")
            ok = patch_file(output_path, log_cb=self._log)
            if not ok:
                self._log("Patch failed.")
                self._finish(success=False, output_path=None)
                return

            # Done
            self._set_progress(1.0)
            self._set_progress_pct("100%")

            in_mb  = os.path.getsize(input_path)  / (1024 * 1024)
            out_mb = os.path.getsize(output_path) / (1024 * 1024)

            self._log("─" * 52)
            self._log("COMPLETE")
            self._log(f"  Input    {os.path.basename(input_path)}  ({in_mb:.1f} MB)")
            self._log(f"  Output   {os.path.basename(output_path)}  ({out_mb:.1f} MB)")
            self._log("─" * 52)
            self._log("Ready to upload at tiktok.com")
            self._log("More options → Upload HD = ON")
            self._finish(success=True, output_path=output_path)

        except Exception as e:
            self._log(f"Unexpected error: {e}")
            self._finish(success=False, output_path=None)

    def _finish(self, success, output_path=None):
        self.processing = False
        def _upd():
            self.process_btn.configure(
                state="normal" if self.file_loaded else "disabled",
                fg_color=C_GREEN if self.file_loaded else C_GREEN_DIS,
                text_color=C_BG if self.file_loaded else C_GREEN_DIM,
                text="⚡   PROCESS VIDEO",
            )
            if success:
                self.progress.configure(progress_color=C_GREEN)
                self._set_progress_label("✓  Completed — ready to upload")
                self.progress_label.configure(text_color=C_GREEN)
                folder = os.path.dirname(output_path)
                name   = os.path.basename(output_path)
                messagebox.showinfo(
                    "✓  Video ready",
                    f"Your video is ready!\n\n"
                    f"File:    {name}\n"
                    f"Folder:  {folder}\n\n"
                    f"Upload at tiktok.com → More options → Upload HD = ON"
                )
            else:
                self.progress.configure(progress_color=C_RED)
                self._set_progress_label("✗  Failed — check log above")
                self.progress_label.configure(text_color=C_RED)
        self.after(0, _upd)

    def _on_progress(self, value):
        self._set_progress(value / 100)
        self._set_progress_pct(f"{int(value)}%")
        if value < 50:
            self._set_progress_label("Copying file...")
        elif value < 85:
            self._set_progress_label("Copying file...")
        else:
            self._set_progress_label("Applying patch...")

    # ──────────────────────────────────────────────────
    #  THREAD-SAFE HELPERS
    # ──────────────────────────────────────────────────

    def _log(self, msg):
        def _ins():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _ins)

    def _log_clear(self):
        def _clr():
            self.log_box.configure(state="normal")
            self.log_box.delete("1.0", "end")
            self.log_box.configure(state="disabled")
        self.after(0, _clr)

    def _set_progress(self, v):
        self.after(0, lambda: self.progress.set(v))

    def _set_progress_label(self, t):
        self.after(0, lambda: self.progress_label.configure(text=t))

    def _set_progress_pct(self, t):
        self.after(0, lambda: self.progress_pct.configure(text=t))