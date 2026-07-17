"""Local OCR selector for copying text from non-selectable surfaces."""

from __future__ import annotations

import asyncio
import base64
import ctypes
import io
import os
import threading
import tkinter as tk
import winsound
from dataclasses import dataclass
from typing import Optional

import win32clipboard
from PIL import Image, ImageEnhance, ImageGrab, ImageOps, ImageTk
from winrt.windows.globalization import Language
from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.security.cryptography import CryptographicBuffer


def capture_screen_data_url() -> dict:
    """Capture the virtual desktop natively without browser sharing permission."""
    image = ImageGrab.grab(all_screens=True).convert("RGB")
    max_edge = 2560
    if max(image.size) > max_edge:
        scale = max_edge / max(image.size)
        image = image.resize(
            (round(image.width * scale), round(image.height * scale)),
            Image.Resampling.LANCZOS,
        )
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=84, optimize=True)
    payload = output.getvalue()
    return {
        "dataUrl": "data:image/jpeg;base64,"
        + base64.b64encode(payload).decode("ascii"),
        "size": len(payload),
        "width": image.width,
        "height": image.height,
    }


@dataclass(frozen=True)
class Selection:
    left: int
    top: int
    right: int
    bottom: int


class UniversalCopyService:
    """Capture a region, OCR it locally, and copy the result."""

    MIN_SIZE = 8

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active = False

    def trigger(self, ai_callback=None) -> bool:
        """Launch without blocking Aura's global hotkey listener."""
        with self._lock:
            if self._active:
                winsound.MessageBeep(winsound.MB_ICONWARNING)
                return False
            self._active = True
        threading.Thread(
            target=self._run,
            args=(ai_callback,),
            name="AuraUniversalCopy",
            daemon=True,
        ).start()
        return True

    def _run(self, ai_callback=None) -> None:
        try:
            screenshot = ImageGrab.grab(all_screens=True)
            selection = self._select_region(screenshot)
            if selection is None:
                return
            region = screenshot.crop(
                (selection.left, selection.top, selection.right, selection.bottom)
            )
            text = self._recognize(region)
            if not text:
                winsound.MessageBeep(winsound.MB_ICONWARNING)
                self._toast("No text found", "Try a tighter or larger selection.", False)
                return
            self._copy(text)
            if ai_callback:
                ai_callback(text)
            winsound.MessageBeep(winsound.MB_OK)
            lines = text.count("\n") + 1
            self._toast(
                "Sent to Aura AI" if ai_callback else "Text copied",
                (
                    f"{len(text)} characters copied and queued for AI."
                    if ai_callback
                    else f"{len(text)} characters, {lines} line{'s' if lines != 1 else ''}. Press Ctrl+V to paste."
                ),
                True,
            )
            print(f"Universal Copy: copied {len(text)} characters from {lines} line(s)")
        except Exception as exc:
            winsound.MessageBeep(winsound.MB_ICONERROR)
            print(f"Universal Copy failed: {exc}")
            self._toast("Universal Copy failed", str(exc)[:120], False)
        finally:
            with self._lock:
                self._active = False

    def _select_region(self, screenshot: Image.Image) -> Optional[Selection]:
        """Show a frozen virtual-desktop overlay and return image-space bounds."""
        user32 = ctypes.windll.user32
        virtual_left = user32.GetSystemMetrics(76)
        virtual_top = user32.GetSystemMetrics(77)
        virtual_width = user32.GetSystemMetrics(78) or screenshot.width
        virtual_height = user32.GetSystemMetrics(79) or screenshot.height

        # Tk may use logical coordinates on mixed-DPI systems. The selected
        # rectangle is mapped back to the full-resolution screen grab below.
        preview = screenshot.resize(
            (virtual_width, virtual_height), Image.Resampling.LANCZOS
        )
        preview = ImageEnhance.Brightness(preview).enhance(0.52)

        root = tk.Tk()
        root.withdraw()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.configure(cursor="crosshair")
        root.geometry(f"{virtual_width}x{virtual_height}+0+0")
        root.deiconify()
        root.update_idletasks()
        user32.SetWindowPos(
            root.winfo_id(), -1, virtual_left, virtual_top,
            virtual_width, virtual_height, 0x0040,
        )

        canvas = tk.Canvas(root, highlightthickness=0, cursor="crosshair")
        canvas.pack(fill="both", expand=True)
        preview_photo = ImageTk.PhotoImage(preview)
        canvas.create_image(0, 0, image=preview_photo, anchor="nw")
        canvas.preview_photo = preview_photo
        banner = canvas.create_rectangle(
            18, 18, 510, 76, fill="#10131a", outline="#39e6c8", width=2
        )
        hint = canvas.create_text(
            34, 46, anchor="w", fill="white",
            font=("Segoe UI", 13, "bold"),
            text="UNIVERSAL COPY  |  Drag over text  |  Esc to cancel",
        )
        state = {"start": None, "box": None, "label": None, "result": None}

        def cancel(_event=None):
            state["result"] = None
            root.quit()

        def press(event):
            state["start"] = (event.x, event.y)
            canvas.delete(banner)
            canvas.delete(hint)
            state["box"] = canvas.create_rectangle(
                event.x, event.y, event.x, event.y,
                outline="#39e6c8", width=3, fill="white", stipple="gray75",
            )
            state["label"] = canvas.create_text(
                event.x + 8, event.y - 8, anchor="sw", fill="white",
                font=("Segoe UI", 10, "bold"), text="",
            )

        def drag(event):
            if state["start"] is None:
                return
            start_x, start_y = state["start"]
            canvas.coords(
                state["box"], start_x, start_y, event.x, event.y
            )
            canvas.coords(
                state["label"],
                min(start_x, event.x) + 8,
                min(start_y, event.y) - 8,
            )
            canvas.itemconfigure(
                state["label"],
                text=f"{abs(event.x - start_x)} x {abs(event.y - start_y)}",
            )

        def release(event):
            if state["start"] is None:
                return
            start_x, start_y = state["start"]
            left, right = sorted(
                (max(0, start_x), min(virtual_width, event.x))
            )
            top, bottom = sorted(
                (max(0, start_y), min(virtual_height, event.y))
            )
            if right - left < self.MIN_SIZE or bottom - top < self.MIN_SIZE:
                cancel()
                return
            scale_x = screenshot.width / virtual_width
            scale_y = screenshot.height / virtual_height
            state["result"] = Selection(
                max(0, round(left * scale_x)),
                max(0, round(top * scale_y)),
                min(screenshot.width, round(right * scale_x)),
                min(screenshot.height, round(bottom * scale_y)),
            )
            root.quit()

        canvas.bind("<ButtonPress-1>", press)
        canvas.bind("<B1-Motion>", drag)
        canvas.bind("<ButtonRelease-1>", release)
        canvas.bind("<ButtonPress-3>", cancel)
        root.bind("<Escape>", cancel)
        root.focus_force()
        root.grab_set()
        try:
            root.mainloop()
        finally:
            try:
                root.grab_release()
            except tk.TclError:
                pass
            root.destroy()
        return state["result"]

    def _recognize(self, image: Image.Image) -> str:
        """Run Windows OCR locally and choose the best installed language."""
        grayscale = ImageOps.autocontrast(image.convert("L"))
        longest_edge = max(grayscale.size)
        if longest_edge < 1800:
            scale = min(3.0, 1800 / max(1, longest_edge))
            grayscale = grayscale.resize(
                (
                    round(grayscale.width * scale),
                    round(grayscale.height * scale),
                ),
                Image.Resampling.LANCZOS,
            )
        if max(grayscale.size) > OcrEngine.max_image_dimension:
            scale = OcrEngine.max_image_dimension / max(grayscale.size)
            grayscale = grayscale.resize(
                (
                    round(grayscale.width * scale),
                    round(grayscale.height * scale),
                ),
                Image.Resampling.LANCZOS,
            )

        rgba = grayscale.convert("RGBA")
        encoded = base64.b64encode(rgba.tobytes()).decode("ascii")
        buffer = CryptographicBuffer.decode_from_base64_string(encoded)
        bitmap = SoftwareBitmap.create_copy_from_buffer(
            buffer, BitmapPixelFormat.RGBA8, rgba.width, rgba.height
        )

        requested = os.environ.get(
            "UNIVERSAL_COPY_LANGUAGE", "auto"
        ).strip()
        engines = []
        if requested and requested.lower() != "auto":
            language = Language(requested)
            if OcrEngine.is_language_supported(language):
                engine = OcrEngine.try_create_from_language(language)
                if engine:
                    engines.append((language.language_tag, engine))

        if not engines:
            profile = OcrEngine.try_create_from_user_profile_languages()
            if profile:
                engines.append(
                    (profile.recognizer_language.language_tag, profile)
                )
            seen = {tag.lower() for tag, _ in engines}
            for language in OcrEngine.available_recognizer_languages:
                if language.language_tag.lower() in seen:
                    continue
                engine = OcrEngine.try_create_from_language(language)
                if engine:
                    engines.append((language.language_tag, engine))

        if not engines:
            raise RuntimeError("No Windows OCR language pack is installed.")

        loop = asyncio.new_event_loop()
        try:
            candidates = []
            for language_tag, engine in engines:
                result = loop.run_until_complete(
                    engine.recognize_async(bitmap)
                )
                text = self._normalize(result.text)
                candidates.append(
                    (self._language_score(text, language_tag), text)
                )
        finally:
            loop.close()
        return max(
            candidates, default=(0.0, ""), key=lambda item: item[0]
        )[1]

    @staticmethod
    def _normalize(text: str) -> str:
        lines = [
            line.rstrip()
            for line in text.replace("\r\n", "\n").split("\n")
        ]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        return "\n".join(lines)

    @staticmethod
    def _language_score(text: str, language_tag: str) -> float:
        visible = [char for char in text if not char.isspace()]
        if not visible:
            return 0.0
        arabic = sum("\u0600" <= char <= "\u06ff" for char in visible)
        latin = sum(
            ("a" <= char.lower() <= "z") or char.isdigit()
            for char in visible
        )
        bonus = arabic if language_tag.lower().startswith("ar") else latin
        return len(visible) + bonus * 1.5 + min(text.count("\n"), 20)

    @staticmethod
    def _copy(text: str) -> None:
        last_error = None
        for _ in range(10):
            try:
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardText(
                        text, win32clipboard.CF_UNICODETEXT
                    )
                finally:
                    win32clipboard.CloseClipboard()
                return
            except Exception as exc:
                last_error = exc
                threading.Event().wait(0.05)
        raise RuntimeError(
            f"Could not access the Windows clipboard: {last_error}"
        )

    @staticmethod
    def _toast(title: str, detail: str, success: bool) -> None:
        """Show brief native feedback without switching back to Aura."""
        try:
            toast = tk.Tk()
            toast.overrideredirect(True)
            toast.attributes("-topmost", True)
            toast.attributes("-alpha", 0.96)
            toast.configure(bg="#10131a")
            frame = tk.Frame(
                toast,
                bg="#10131a",
                highlightbackground="#39e6c8" if success else "#ff6b7a",
                highlightthickness=2,
                padx=18,
                pady=12,
            )
            frame.pack()
            tk.Label(
                frame,
                text=title,
                bg="#10131a",
                fg="#39e6c8" if success else "#ff8a96",
                font=("Segoe UI", 11, "bold"),
            ).pack(anchor="w")
            tk.Label(
                frame,
                text=detail,
                bg="#10131a",
                fg="#e9edf5",
                font=("Segoe UI", 9),
            ).pack(anchor="w", pady=(3, 0))
            toast.update_idletasks()
            width, height = toast.winfo_reqwidth(), toast.winfo_reqheight()
            x = (toast.winfo_screenwidth() - width) // 2
            y = toast.winfo_screenheight() - height - 70
            toast.geometry(f"{width}x{height}+{x}+{y}")
            toast.after(2400, toast.destroy)
            toast.mainloop()
        except Exception as exc:
            print(f"Universal Copy notification failed: {exc}")


universal_copy_service = UniversalCopyService()
