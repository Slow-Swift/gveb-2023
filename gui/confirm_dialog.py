from tkinter import *
from tkinter import ttk

class ConfirmDialog(Toplevel):
    def __init__(self, message, callback, root, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.callback = callback
        confirm_frame = ttk.Frame(self, padding=8)
        confirm_frame.grid(row=0, column=0, sticky=NSEW)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        ttk.Label(confirm_frame, text=message, anchor="center", wraplength=300).grid(row=0, column=0, columnspan=2, sticky=EW)
        ttk.Button(confirm_frame, text="Cancel", command=self.destroy).grid(row=2, column=0)
        ttk.Button(confirm_frame, text="Confirm", command=self.on_done_pressed).grid(row=2, column=1)
        
        self.update_idletasks()
        
        x = root.winfo_x() + int(root.winfo_width() / 2 - self.winfo_width() / 2)
        y = root.winfo_y() + int(root.winfo_height() / 2 - self.winfo_height() / 2)
        self.geometry(f"+{x}+{y}")
        
    def on_done_pressed(self):
        self.destroy()
        self.callback()
