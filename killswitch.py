import tkinter as tk
from tkinter import messagebox
import keyboard
import threading
import pystray
from PIL import Image, ImageDraw
import hashlib
import time
import screeninfo

# --- Configuration ---
SHORTCUT = "ctrl+alt+k"
# The password to dismiss the screen. A good practice is to hash it.
# We'll use SHA-256 for a simple hash.
PASSWORD = "password123"
SALT = b'some_random_salt'  # Add a salt to make it more secure
HASHED_PASSWORD = hashlib.sha256(SALT + PASSWORD.encode()).hexdigest()

class KillswitchWindow:
    """
    Manages a single, large window that covers all monitors.
    """
    def __init__(self, password_hash):
        self.password_hash = password_hash
        self.entry_field = None
        
        # Create a single root window that will cover all monitors.
        self.main_window = tk.Tk()
        self.main_window.title("Killswitch!")
        
        # Make the window borderless and always on top.
        self.main_window.attributes("-topmost", True)
        self.main_window.overrideredirect(True)
        self.main_window.configure(bg="black")

        # Calculate the total width and height of all monitors combined.
        # This is a robust way to ensure the window covers all screens.
        monitors = screeninfo.get_monitors()
        total_width = 0
        total_height = 0
        
        for monitor in monitors:
            # We assume a horizontal arrangement for width, and take the max height
            # for a vertical one. This should be sufficient for most setups.
            if monitor.x + monitor.width > total_width:
                total_width = monitor.x + monitor.width
            if monitor.y + monitor.height > total_height:
                total_height = monitor.y + monitor.height

        # Set the window geometry to cover the entire combined screen area and place it at (0,0).
        self.main_window.geometry(f"{total_width}x{total_height}+0+0")
        
        # Show the message label
        self.show_message_label()
        
        # Bind the click event to the single main window to handle user interaction.
        self.main_window.bind("<Button-1>", self.on_click)

    def show_message_label(self):
        """Displays the 'Killswitch!' message."""
        self.label = tk.Label(self.main_window, text="Killswitch!", font=("Helvetica", 72, "bold"), fg="red", bg="black")
        self.label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def on_click(self, event):
        """Handles the mouse click event to show the password box."""
        if hasattr(self, 'input_frame'):
            return

        if hasattr(self, 'label') and self.label:
            self.label.destroy()
            del self.label
        
        self.input_frame = tk.Frame(self.main_window, bg="black")
        self.input_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        prompt_label = tk.Label(self.input_frame, text="Enter password to deactivate:", font=("Helvetica", 24), fg="white", bg="black")
        prompt_label.pack(pady=10)

        self.entry_field = tk.Entry(self.input_frame, show="*", font=("Helvetica", 24), width=20)
        self.entry_field.pack(pady=10)
        self.entry_field.focus_set()

        submit_button = tk.Button(self.input_frame, text="Submit", command=self.check_password, font=("Helvetica", 18))
        submit_button.pack(pady=10)

        self.entry_field.bind("<Return>", lambda e: self.check_password())

    def check_password(self):
        """Checks the entered password against the stored hash."""
        entered_password = self.entry_field.get()
        entered_password_hash = hashlib.sha256(SALT + entered_password.encode()).hexdigest()
        
        if entered_password_hash == self.password_hash:
            self.main_window.destroy()
        else:
            self.entry_field.delete(0, tk.END)
            messagebox.showerror("Error", "Incorrect password")

def create_tray_icon():
    """Creates the system tray icon with menu options."""
    global is_listener_active
    
    image = Image.new('RGB', (64, 64), color='black')
    d = ImageDraw.Draw(image)
    d.rectangle((16, 16, 48, 48), fill='red')

    def toggle_listener_action(icon, item):
        global is_listener_active
        if is_listener_active:
            keyboard.unhook_all()
            is_listener_active = False
            item.text = "Start Listener"
        else:
            keyboard.add_hotkey(SHORTCUT, on_hotkey_press)
            is_listener_active = True
            item.text = "Stop Listener"
    
    def on_quit(icon, item):
        icon.stop()
        keyboard.unhook_all()
        exit()

    menu = (pystray.MenuItem(f"Stop Listener", toggle_listener_action),
            pystray.MenuItem("Quit", on_quit))
    
    icon = pystray.Icon("killswitch", image, "Killswitch", menu)
    icon.run()

def on_hotkey_press():
    """
    This function is called when the hotkey is pressed.
    It creates and runs the killswitch window in a new thread.
    """
    keyboard.unhook_all()
    
    window_instance = KillswitchWindow(HASHED_PASSWORD)
    window_instance.main_window.mainloop()
    
    keyboard.add_hotkey(SHORTCUT, on_hotkey_press)

if __name__ == "__main__":
    is_listener_active = True
    
    tray_thread = threading.Thread(target=create_tray_icon, daemon=True)
    tray_thread.start()
    
    keyboard.add_hotkey(SHORTCUT, on_hotkey_press)
    print(f"Killswitch is running. Press '{SHORTCUT}' to activate.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        keyboard.unhook_all()
