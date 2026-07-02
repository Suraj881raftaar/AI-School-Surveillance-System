import tkinter as tk
from tkinter import messagebox
import sqlite3
from config import *

# ----------------------------
# Window
# ----------------------------
root = tk.Tk()

root.title(APP_NAME + " - Login")
root.geometry("700x500")
root.configure(bg=BG_COLOR)
root.resizable(False, False)

# ----------------------------
# Database Login Function
# ----------------------------
def login():

    username = username_entry.get()
    password = password_entry.get()

    if username == "" or password == "":
        messagebox.showwarning(
            "Warning",
            "Please enter Username and Password"
        )
        return

    try:

        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()

        cur.execute(
            """
            SELECT * FROM users
            WHERE username=? AND password=?
            """,
            (
                username,
                password
            )
        )

        user = cur.fetchone()

        conn.close()

        if user:

            messagebox.showinfo(
                "Success",
                "Login Successful"
            )

            root.destroy()

            import main
            main.run_application()

        else:

            messagebox.showerror(
                "Login Failed",
                "Invalid Username or Password"
            )

    except Exception as e:

        messagebox.showerror(
            "Database Error",
            str(e)
        )

# ----------------------------
# Show Password
# ----------------------------
def toggle_password():

    if password_entry.cget("show") == "*":

        password_entry.config(show="")

        show_btn.config(text="Hide")

    else:

        password_entry.config(show="*")

        show_btn.config(text="Show")
        # ----------------------------
# Title
# ----------------------------
title = tk.Label(
    root,
    text="AI SCHOOL SURVEILLANCE SYSTEM",
    font=TITLE_FONT,
    bg=BG_COLOR,
    fg=HEADER_COLOR
)

title.pack(pady=40)

# ----------------------------
# Login Frame
# ----------------------------
frame = tk.Frame(
    root,
    bg="white",
    padx=40,
    pady=30,
    relief="ridge",
    bd=2
)

frame.pack()

# Username
tk.Label(
    frame,
    text="Username",
    font=LABEL_FONT,
    bg="white"
).grid(row=0, column=0, sticky="w", pady=10)

username_entry = tk.Entry(
    frame,
    font=LABEL_FONT,
    width=30
)

username_entry.grid(row=0, column=1, pady=10)

# Password
tk.Label(
    frame,
    text="Password",
    font=LABEL_FONT,
    bg="white"
).grid(row=1, column=0, sticky="w", pady=10)

password_entry = tk.Entry(
    frame,
    font=LABEL_FONT,
    width=30,
    show="*"
)

password_entry.grid(row=1, column=1, pady=10)

show_btn = tk.Button(
    frame,
    text="Show",
    width=8,
    command=toggle_password
)

show_btn.grid(row=1, column=2, padx=5)

# Login Button
login_btn = tk.Button(
    root,
    text="LOGIN",
    width=20,
    bg=BUTTON_COLOR,
    fg="white",
    font=BUTTON_FONT,
    command=login
)

login_btn.pack(pady=30)

# Footer
footer = tk.Label(
    root,
    text="AI Based School Surveillance & Attendance System",
    bg=BG_COLOR,
    fg="gray",
    font=("Arial", 10)
)

footer.pack(side="bottom", pady=20)

# Press Enter to Login
root.bind("<Return>", lambda event: login())

username_entry.focus()

root.mainloop()
