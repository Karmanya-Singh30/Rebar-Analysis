import customtkinter as ctk
from tkinter import filedialog
import subprocess
import threading
import os
import sys

# Set modern theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class RebarApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Rebar Analysis & AI Comparison Tool")
        self.geometry("800x650")
        self.grid_columnconfigure(1, weight=1)

        # --- Variables ---
        self.input_path_var = ctk.StringVar()
        default_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result.jpg")
        self.output_path_var = ctk.StringVar(value=default_out)
        self.compare_path_var = ctk.StringVar()

        # --- UI Layout ---
        self.create_widgets()

    def create_widgets(self):
        # Header
        header_label = ctk.CTkLabel(self, text="Rebar Analyzer Pro", font=ctk.CTkFont(size=24, weight="bold"))
        header_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 10), sticky="w")

        # --- Input File Row ---
        ctk.CTkLabel(self, text="1. Input Photo:").grid(row=1, column=0, padx=20, pady=10, sticky="e")
        self.input_entry = ctk.CTkEntry(self, textvariable=self.input_path_var, placeholder_text="Select rebar photograph...")
        self.input_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self, text="Browse", command=self.browse_input).grid(row=1, column=2, padx=20, pady=10)

        # --- Output File Row ---
        ctk.CTkLabel(self, text="2. Save Result As:").grid(row=2, column=0, padx=20, pady=10, sticky="e")
        self.output_entry = ctk.CTkEntry(self, textvariable=self.output_path_var)
        self.output_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self, text="Browse", command=self.browse_output).grid(row=2, column=2, padx=20, pady=10)

        # --- Compare File Row (Optional) ---
        ctk.CTkLabel(self, text="3. Architect Design:").grid(row=3, column=0, padx=20, pady=10, sticky="e")
        self.compare_entry = ctk.CTkEntry(self, textvariable=self.compare_path_var, placeholder_text="(Optional) Select design for Gemini comparison...")
        self.compare_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self, text="Browse", command=self.browse_compare).grid(row=3, column=2, padx=20, pady=10)

        # --- Run Button ---
        self.run_btn = ctk.CTkButton(self, text="Run Analysis", font=ctk.CTkFont(size=16, weight="bold"), height=40, command=self.start_analysis_thread)
        self.run_btn.grid(row=4, column=0, columnspan=3, padx=20, pady=20, sticky="ew")

        # --- Console Output Terminal ---
        ctk.CTkLabel(self, text="Terminal Output & Results:").grid(row=5, column=0, columnspan=3, padx=20, pady=(10, 0), sticky="w")
        self.console_text = ctk.CTkTextbox(self, height=250, state="disabled", font=("Consolas", 12))
        self.console_text.grid(row=6, column=0, columnspan=3, padx=20, pady=(5, 20), sticky="nsew")
        self.grid_rowconfigure(6, weight=1)

    # --- File Browsing Methods ---
    def browse_input(self):
        filepath = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if filepath:
            self.input_path_var.set(filepath)

    def browse_output(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG", "*.jpg")])
        if filepath:
            self.output_path_var.set(filepath)

    def browse_compare(self):
        filepath = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if filepath:
            self.compare_path_var.set(filepath)

    # --- Execution Logic ---
    def log_to_console(self, message):
        """Helper to append text to the disabled textbox."""
        self.console_text.configure(state="normal")
        self.console_text.insert("end", message + "\n")
        self.console_text.see("end")
        self.console_text.configure(state="disabled")

    def start_analysis_thread(self):
        input_path = self.input_path_var.get()
        if not input_path or not os.path.exists(input_path):
            self.log_to_console("[ERROR] Please select a valid input photo.")
            return

        self.run_btn.configure(state="disabled", text="Running...")
        self.console_text.configure(state="normal")
        self.console_text.delete("1.0", "end")
        self.console_text.configure(state="disabled")
        self.log_to_console(">>> Starting Master Script...")

        thread = threading.Thread(target=self.run_master_script)
        thread.start()

    def run_master_script(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        main_script_path = os.path.join(current_dir, "main.py")

        cmd = [sys.executable, "-X", "utf8", main_script_path, 
               "--input", self.input_path_var.get(), 
               "--output", self.output_path_var.get()]
        
        compare_path = self.compare_path_var.get()
        if compare_path:
            cmd.extend(["--compare", compare_path])

        custom_env = os.environ.copy()
        custom_env["PYTHONUTF8"] = "1"
        custom_env["PYTHONIOENCODING"] = "utf-8"

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                     text=True, encoding='utf-8', bufsize=1, env=custom_env)
            
            for line in process.stdout:
                self.after(0, self.log_to_console, line.strip())
            
            process.wait()
            if process.returncode == 0:
                self.after(0, self.log_to_console, "\n>>> Process Completed Successfully!")
            else:
                self.after(0, self.log_to_console, f"\n>>> Process exited with error code: {process.returncode}")
                
        except Exception as e:
            self.after(0, self.log_to_console, f"[CRITICAL ERROR] {str(e)}")
            
        finally:
            self.after(0, lambda: self.run_btn.configure(state="normal", text="Run Analysis"))

if __name__ == "__main__":
    app = RebarApp()
    app.mainloop()