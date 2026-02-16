import customtkinter as ctk
import subprocess
import threading
import sys
import os
from tkinter import END

# Set appearance mode and color theme
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class BotLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Monster Bot Launcher")
        self.geometry("700x500")
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Monster Bot Control Panel", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=10)
        
        self.status_label = ctk.CTkLabel(self.header_frame, text="Status: Stopped", text_color="red", font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=5)

        # Console Output
        self.console_textbox = ctk.CTkTextbox(self, width=650, height=300)
        self.console_textbox.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.console_textbox.configure(state="disabled")

        # Buttons
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=2, column=0, padx=20, pady=20, sticky="ew")

        self.start_button = ctk.CTkButton(self.button_frame, text="Start Bot", command=self.start_bot, fg_color="green", hover_color="darkgreen")
        self.start_button.pack(side="left", padx=20, pady=10, expand=True)

        self.stop_button = ctk.CTkButton(self.button_frame, text="Stop Bot", command=self.stop_bot, fg_color="red", hover_color="darkred", state="disabled")
        self.stop_button.pack(side="right", padx=20, pady=10, expand=True)

        self.process = None

    def log(self, message):
        self.console_textbox.configure(state="normal")
        self.console_textbox.insert(END, message + "\n")
        self.console_textbox.see(END)
        self.console_textbox.configure(state="disabled")

    def run_process(self):
         # Determine python executable
        python_exec = sys.executable
        
        # Run bot.py
        try:
            self.process = subprocess.Popen(
                [python_exec, "bot.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            ) 

            # Read stdout
            for line in iter(self.process.stdout.readline, ''):
                self.log(line.strip())
            
            # Read stderr
            for line in iter(self.process.stderr.readline, ''):
                self.log(f"ERROR: {line.strip()}")
                
            self.process.stdout.close()
            self.process.wait()
            
            self.bot_stopped()

        except Exception as e:
            self.log(f"Failed to start bot: {e}")
            self.bot_stopped()

    def start_bot(self):
        self.status_label.configure(text="Status: Running", text_color="green")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.log("--- Starting Bot ---")
        
        self.thread = threading.Thread(target=self.run_process, daemon=True)
        self.thread.start()

    def stop_bot(self):
        if self.process:
            self.process.terminate()
            self.process = None
        self.bot_stopped()
        self.log("--- Bot Stopped ---")

    def bot_stopped(self):
        self.status_label.configure(text="Status: Stopped", text_color="red")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

if __name__ == "__main__":
    app = BotLauncher()
    app.mainloop()
