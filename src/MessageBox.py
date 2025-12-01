from tkinter import messagebox
from enum import Enum
import tkinter as tk

class MessageTypes(Enum):
    INFO = 1
    WARNING = 2
    ERROR = 3

def showMessage(messageType, title, message):
    root = tk.Tk()
    root.withdraw()

    match messageType:
        case MessageTypes.INFO:
            messagebox.showinfo(title, message)

        case MessageTypes.WARNING:
            messagebox.showwarning(title, message)

        case MessageTypes.ERROR:
            messagebox.showerror(title, message)

        case _:
            messagebox.showinfo(title, message)

    root.destroy()
