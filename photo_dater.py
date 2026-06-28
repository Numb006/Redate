import tkinter as tk
from tkinter import ttk, messagebox
import os
import datetime
import threading

# Try to import tkinterdnd2 for drag and drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

SUPPORTED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
    '.webp', '.heic', '.heif', '.raw', '.cr2', '.nef', '.arw',
    '.mp4', '.mov', '.avi', '.mkv'
}

BG = "#1a1a2e"
BG2 = "#16213e"
ACCENT = "#0f3460"
HIGHLIGHT = "#e94560"
TEXT = "#eaeaea"
TEXT_DIM = "#888"
GREEN = "#4ecca3"
BORDER = "#2a2a4a"


class PhotoDaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📅 Foto-Datierung")
        self.root.geometry("800x620")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.photos = []  # list of dicts: {path, filename, current_date}
        self.drag_source_index = None

        self._build_ui()

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────
        header = tk.Frame(self.root, bg=BG, pady=12)
        header.pack(fill="x", padx=20)

        tk.Label(header, text="📅 Foto-Datierung", font=("Segoe UI", 18, "bold"),
                 bg=BG, fg=TEXT).pack(side="left")

        btn_reset = tk.Button(header, text="🔄  Reset", font=("Segoe UI", 10),
                              bg=HIGHLIGHT, fg="white", relief="flat",
                              padx=14, pady=6, cursor="hand2",
                              command=self._reset)
        btn_reset.pack(side="right")

        # ── Drop Zone ────────────────────────────────────────────
        self.drop_frame = tk.Frame(self.root, bg=ACCENT, bd=0, relief="flat",
                                   height=90)
        self.drop_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.drop_frame.pack_propagate(False)

        self.drop_label = tk.Label(
            self.drop_frame,
            text="⬇️  Fotos hier hineinziehen  (oder klicken zum Auswählen)",
            font=("Segoe UI", 12), bg=ACCENT, fg=TEXT, cursor="hand2"
        )
        self.drop_label.pack(expand=True)
        self.drop_frame.bind("<Button-1>", self._open_file_dialog)
        self.drop_label.bind("<Button-1>", self._open_file_dialog)

        # Register drag-and-drop if available
        if HAS_DND:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self._on_drop)
            self.drop_label.drop_target_register(DND_FILES)
            self.drop_label.dnd_bind('<<Drop>>', self._on_drop)

        # ── List Area ────────────────────────────────────────────
        list_frame = tk.Frame(self.root, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Column headers
        header_row = tk.Frame(list_frame, bg=BG2, pady=6)
        header_row.pack(fill="x")
        tk.Label(header_row, text="  #", width=4, anchor="w",
                 font=("Segoe UI", 9, "bold"), bg=BG2, fg=TEXT_DIM).pack(side="left")
        tk.Label(header_row, text="Dateiname", width=35, anchor="w",
                 font=("Segoe UI", 9, "bold"), bg=BG2, fg=TEXT_DIM).pack(side="left")
        tk.Label(header_row, text="Aktuelles Datum", width=22, anchor="w",
                 font=("Segoe UI", 9, "bold"), bg=BG2, fg=TEXT_DIM).pack(side="left")
        tk.Label(header_row, text="↕ ziehen zum Sortieren", anchor="w",
                 font=("Segoe UI", 9), bg=BG2, fg=TEXT_DIM).pack(side="left")

        # Scrollable list
        canvas_frame = tk.Frame(list_frame, bg=BG, relief="flat", bd=1)
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=BG2, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical",
                                  command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.list_inner = tk.Frame(self.canvas, bg=BG2)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.list_inner, anchor="nw")
        self.list_inner.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.empty_label = tk.Label(
            self.list_inner,
            text="Noch keine Fotos – ziehe Dateien in den Bereich oben.",
            font=("Segoe UI", 11), bg=BG2, fg=TEXT_DIM, pady=40
        )
        self.empty_label.pack()

        # ── Date/Time Controls ───────────────────────────────────
        ctrl = tk.Frame(self.root, bg=BG, pady=10)
        ctrl.pack(fill="x", padx=20, pady=(0, 14))

        tk.Label(ctrl, text="Neues Datum & Uhrzeit für ALLE Fotos:",
                 font=("Segoe UI", 11, "bold"), bg=BG, fg=TEXT).pack(side="left", padx=(0, 16))

        # Date entry
        tk.Label(ctrl, text="Datum:", font=("Segoe UI", 10), bg=BG, fg=TEXT_DIM).pack(side="left")
        self.date_var = tk.StringVar(value=datetime.date.today().strftime("%d.%m.%Y"))
        date_entry = tk.Entry(ctrl, textvariable=self.date_var, width=12,
                              font=("Segoe UI", 11), bg=ACCENT, fg=TEXT,
                              insertbackground=TEXT, relief="flat", bd=6)
        date_entry.pack(side="left", padx=(4, 14))

        tk.Label(ctrl, text="Uhrzeit:", font=("Segoe UI", 10), bg=BG, fg=TEXT_DIM).pack(side="left")
        self.time_var = tk.StringVar(value="12:00")
        time_entry = tk.Entry(ctrl, textvariable=self.time_var, width=8,
                              font=("Segoe UI", 11), bg=ACCENT, fg=TEXT,
                              insertbackground=TEXT, relief="flat", bd=6)
        time_entry.pack(side="left", padx=(4, 20))

        tk.Label(ctrl, text="(TT.MM.JJJJ  HH:MM)",
                 font=("Segoe UI", 9), bg=BG, fg=TEXT_DIM).pack(side="left", padx=(0, 20))

        self.btn_apply = tk.Button(
            ctrl, text="✅  Datum anwenden", font=("Segoe UI", 11, "bold"),
            bg=GREEN, fg="#111", relief="flat", padx=18, pady=8,
            cursor="hand2", command=self._apply_dates
        )
        self.btn_apply.pack(side="right")

        # Status bar
        self.status_var = tk.StringVar(value="Bereit.")
        tk.Label(self.root, textvariable=self.status_var,
                 font=("Segoe UI", 9), bg=BG, fg=TEXT_DIM,
                 anchor="w").pack(fill="x", padx=22, pady=(0, 8))

    # ── File Handling ────────────────────────────────────────────

    def _open_file_dialog(self, event=None):
        from tkinter import filedialog
        files = filedialog.askopenfilenames(
            title="Fotos auswählen",
            filetypes=[("Bilddateien", " ".join(f"*{e}" for e in SUPPORTED_EXTENSIONS)),
                       ("Alle Dateien", "*.*")]
        )
        if files:
            self._add_files(list(files))

    def _on_drop(self, event):
        raw = event.data
        # Parse paths (may be space-separated or brace-quoted)
        paths = []
        if raw.startswith("{"):
            import re
            paths = re.findall(r'\{([^}]+)\}|(\S+)', raw)
            paths = [a or b for a, b in paths]
        else:
            paths = raw.split()
        self._add_files(paths)

    def _add_files(self, paths):
        added = 0
        for path in paths:
            path = path.strip()
            ext = os.path.splitext(path)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            if any(p['path'] == path for p in self.photos):
                continue  # skip duplicates
            try:
                mtime = os.path.getmtime(path)
                dt = datetime.datetime.fromtimestamp(mtime)
                date_str = dt.strftime("%d.%m.%Y  %H:%M")
            except Exception:
                date_str = "Unbekannt"
            self.photos.append({
                'path': path,
                'filename': os.path.basename(path),
                'current_date': date_str
            })
            added += 1
        if added:
            self._refresh_list()
            self.status_var.set(f"{added} Foto(s) hinzugefügt – gesamt {len(self.photos)}.")

    # ── List Rendering ───────────────────────────────────────────

    def _refresh_list(self):
        for widget in self.list_inner.winfo_children():
            widget.destroy()

        if not self.photos:
            self.empty_label = tk.Label(
                self.list_inner,
                text="Noch keine Fotos – ziehe Dateien in den Bereich oben.",
                font=("Segoe UI", 11), bg=BG2, fg=TEXT_DIM, pady=40
            )
            self.empty_label.pack()
            return

        for i, photo in enumerate(self.photos):
            self._build_row(i, photo)

    def _build_row(self, i, photo):
        row_bg = BG2 if i % 2 == 0 else ACCENT
        row = tk.Frame(self.list_inner, bg=row_bg, pady=5, cursor="fleur")
        row.pack(fill="x")

        tk.Label(row, text=f"  {i+1}", width=4, anchor="w",
                 font=("Segoe UI", 10), bg=row_bg, fg=TEXT_DIM).pack(side="left")

        tk.Label(row, text=photo['filename'], width=35, anchor="w",
                 font=("Segoe UI", 10), bg=row_bg, fg=TEXT).pack(side="left")

        tk.Label(row, text=photo['current_date'], width=22, anchor="w",
                 font=("Segoe UI", 10), bg=row_bg, fg=TEXT_DIM).pack(side="left")

        # Drag handle
        handle = tk.Label(row, text="⠿", font=("Segoe UI", 14),
                          bg=row_bg, fg=TEXT_DIM, cursor="fleur", padx=8)
        handle.pack(side="left")

        # Remove button
        def make_remove(idx):
            return lambda: self._remove_photo(idx)
        tk.Button(row, text="✕", font=("Segoe UI", 9), bg=row_bg, fg=HIGHLIGHT,
                  relief="flat", cursor="hand2", bd=0, padx=6,
                  command=make_remove(i)).pack(side="right", padx=8)

        # Drag bindings on whole row
        for widget in [row] + list(row.winfo_children()):
            widget.bind("<ButtonPress-1>", lambda e, idx=i: self._drag_start(idx))
            widget.bind("<B1-Motion>", lambda e, idx=i: self._drag_motion(e, idx))
            widget.bind("<ButtonRelease-1>", self._drag_end)

    def _remove_photo(self, idx):
        del self.photos[idx]
        self._refresh_list()
        self.status_var.set(f"{len(self.photos)} Foto(s) in der Liste.")

    # ── Drag & Drop (in-list reordering) ────────────────────────

    def _drag_start(self, idx):
        self.drag_source_index = idx

    def _drag_motion(self, event, idx):
        pass  # visual feedback could be added here

    def _drag_end(self, event):
        if self.drag_source_index is None:
            return
        # Determine target row from mouse Y position
        y = self.canvas.canvasy(event.y_root - self.canvas.winfo_rooty())
        rows = self.list_inner.winfo_children()
        target = None
        for i, row in enumerate(rows):
            ry = row.winfo_y()
            rh = row.winfo_height()
            if ry <= y < ry + rh:
                target = i
                break
        if target is None:
            target = len(self.photos) - 1

        src = self.drag_source_index
        if src != target:
            photo = self.photos.pop(src)
            self.photos.insert(target, photo)
            self._refresh_list()
            self.status_var.set(f"Reihenfolge geändert: '{photo['filename']}' → Position {target+1}")
        self.drag_source_index = None

    # ── Apply Dates ──────────────────────────────────────────────

    def _apply_dates(self):
        if not self.photos:
            messagebox.showwarning("Keine Fotos", "Bitte zuerst Fotos hinzufügen.")
            return

        date_str = self.date_var.get().strip()
        time_str = self.time_var.get().strip()

        try:
            dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
        except ValueError:
            messagebox.showerror("Ungültiges Format",
                                 "Bitte Datum als TT.MM.JJJJ und Uhrzeit als HH:MM eingeben.")
            return

        result = messagebox.askyesno(
            "Bestätigung",
            f"Datum & Uhrzeit auf {dt.strftime('%d.%m.%Y %H:%M')} setzen\n"
            f"für {len(self.photos)} Foto(s)?\n\n"
            "⚠️  Originaldateien werden überschrieben!"
        )
        if not result:
            return

        self.btn_apply.config(state="disabled", text="⏳ Wird angewendet…")
        threading.Thread(target=self._do_apply, args=(dt,), daemon=True).start()

    def _do_apply(self, dt):
        timestamp = dt.timestamp()
        success, failed = 0, []

        for photo in self.photos:
            try:
                os.utime(photo['path'], (timestamp, timestamp))
                # Update creation time on Windows via ctypes
                self._set_windows_creation_time(photo['path'], dt)
                photo['current_date'] = dt.strftime("%d.%m.%Y  %H:%M")
                success += 1
            except Exception as e:
                failed.append(f"{photo['filename']}: {e}")

        self.root.after(0, self._apply_done, success, failed)

    def _set_windows_creation_time(self, path, dt):
        try:
            import ctypes
            import ctypes.wintypes

            GENERIC_WRITE = 0x40000000
            OPEN_EXISTING = 3
            FILE_ATTRIBUTE_NORMAL = 0x80

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.CreateFileW(
                path, GENERIC_WRITE, 0, None, OPEN_EXISTING,
                FILE_ATTRIBUTE_NORMAL, None
            )
            if handle == ctypes.wintypes.HANDLE(-1).value:
                return  # Can't open, skip (modified time still set)

            # Convert datetime to FILETIME (100-nanosecond intervals since 1601-01-01)
            EPOCH = datetime.datetime(1601, 1, 1)
            delta = dt - EPOCH
            filetime_val = int(delta.total_seconds() * 10_000_000)

            ft = ctypes.wintypes.FILETIME(
                filetime_val & 0xFFFFFFFF,
                (filetime_val >> 32) & 0xFFFFFFFF
            )
            kernel32.SetFileTime(handle, ctypes.byref(ft), None, None)
            kernel32.CloseHandle(handle)
        except Exception:
            pass  # Non-Windows or access denied – modified time is already set

    def _apply_done(self, success, failed):
        self.btn_apply.config(state="normal", text="✅  Datum anwenden")
        self._refresh_list()

        if failed:
            msg = f"{success} erfolgreich.\n\nFehler bei:\n" + "\n".join(failed[:10])
            messagebox.showwarning("Teilweise abgeschlossen", msg)
        else:
            messagebox.showinfo("Fertig! ✅",
                                f"Datum erfolgreich geändert für {success} Foto(s).\n\n"
                                f"Neues Datum: {self.date_var.get()}  {self.time_var.get()}")
        self.status_var.set(f"✅ {success} Foto(s) aktualisiert.")

    # ── Helpers ──────────────────────────────────────────────────

    def _reset(self):
        if self.photos and not messagebox.askyesno("Reset", "Alle Fotos aus der Liste entfernen?"):
            return
        self.photos.clear()
        self._refresh_list()
        self.status_var.set("Liste geleert.")

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# ── Entry Point ──────────────────────────────────────────────────

def main():
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = PhotoDaterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
