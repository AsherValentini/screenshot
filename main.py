import tkinter as tk
from mss import mss
from PIL import Image
import io
import subprocess
import platform
import threading
import keyboard


class StealthSnippingTool:
    def __init__(self):
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.monitors = self.get_monitors()

    def get_monitors(self):
        # Retrieve monitor dimensions using mss
        with mss() as sct:
            return sct.monitors  # List of monitors, including a combined virtual monitor at index 0

    def capture_screen(self):
        # Get dimensions of the virtual screen (all monitors combined)
        virtual_monitor = self.monitors[0]  # Monitor 0 is the full virtual screen
        width = virtual_monitor["width"]
        height = virtual_monitor["height"]
        top = virtual_monitor["top"]
        left = virtual_monitor["left"]

        # Create an invisible fullscreen overlay
        root = tk.Tk()
        root.geometry(f"{width}x{height}+{left}+{top}")
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.01)  # Almost invisible
        root.configure(bg="black")

        # Bind mouse events to capture selection
        root.bind("<ButtonPress-1>", self.on_mouse_down)
        root.bind("<ButtonRelease-1>", self.on_mouse_up)

        # Run the overlay
        root.mainloop()

    def on_mouse_down(self, event):
        # Record the starting mouse position
        self.start_x = event.widget.winfo_pointerx()
        self.start_y = event.widget.winfo_pointery()

    def on_mouse_up(self, event):
        # Record the ending mouse position
        self.end_x = event.widget.winfo_pointerx()
        self.end_y = event.widget.winfo_pointery()

        # Destroy the overlay
        event.widget.quit()
        event.widget.destroy()

        # Capture the screenshot
        self.capture_screenshot()

    def capture_screenshot(self):
        # Ensure coordinates are sorted
        x1, x2 = sorted([self.start_x, self.end_x])
        y1, y2 = sorted([self.start_y, self.end_y])

        # Capture the selected area across all monitors
        monitor = {"top": y1, "left": x1, "width": x2 - x1, "height": y2 - y1}
        with mss() as sct:
            screenshot = sct.grab(monitor)

        # Convert to a PIL image
        image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

        # Save to clipboard
        self.save_to_clipboard(image)

    def save_to_clipboard(self, image):
        # Save the image to a byte buffer in PNG format
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")  # Ensure proper PNG format
        img_buffer.seek(0)

        # Save the image to the clipboard
        system = platform.system()
        if system == "Windows":
            # Use PowerShell to copy the image to the clipboard
            with open("temp_image.png", "wb") as f:
                f.write(img_buffer.getvalue())
            subprocess.run(["powershell", "-c", "Set-Clipboard -Path temp_image.png"])
        elif system == "Darwin":
            # macOS: Use `pbcopy` to copy the image
            p = subprocess.Popen(
                ["osascript", "-e", 'set the clipboard to (read (POSIX file "/tmp/screenshot.png") as JPEG picture)'],
                stdin=subprocess.PIPE,
            )
            p.communicate(input=img_buffer.getvalue())
        else:
            # Linux: Use xclip to copy the image
            p = subprocess.Popen(["xclip", "-selection", "clipboard", "-t", "image/png"], stdin=subprocess.PIPE)
            p.communicate(input=img_buffer.getvalue())

        print("Screenshot copied to clipboard.")

    def run(self):
        while True:
            print("Waiting for hotkey (Ctrl + Alt + Shift)...")
            keyboard.wait("ctrl+alt+shift")  # Wait for hotkey
            print("Hotkey detected. Entering snipping mode.")
            self.capture_screen()


if __name__ == "__main__":
    # Run the snipping tool in a separate thread
    tool = StealthSnippingTool()
    threading.Thread(target=tool.run, daemon=True).start()
    print("Snipping tool running indefinitely.")
    threading.Event().wait()  # Keep the script alive
