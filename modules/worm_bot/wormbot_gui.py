import tkinter as tk
from tkinter import filedialog, messagebox, ttk  # Ensure messagebox is imported
from core.bot import Bot  # Ensure Bot is imported


class WormBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WormBot: Code Analysis and Fixing Tool")
        self.bot = None
        self.is_dark_mode = False  # Flag for dark mode

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.lang_var = tk.StringVar()  # Initialize language variable

        try:
            self.load_bot()  # Load the bot and modules
            self.create_widgets()  # Create GUI widgets only if bot loads successfully
        except Exception as e:
            print(f"Error loading bot: {e}")
            messagebox.showerror("Error", f"Failed to load bot: {e}")
            self.bot = None

    def load_bot(self):
        """Load the bot and modules."""
        print("Debug: Loading bot...")
        self.bot = Bot()  # Initialize Bot
        print("Debug: Bot modules loaded:", self.bot.modules)

        if not self.bot.modules:
            messagebox.showerror(
                "Error",
                "No modules loaded! Check the 'modules' directory for valid module files."
            )
            self.root.destroy()
            return  # Properly indented within the function

        # Set default language if modules exist
        self.lang_var.set(list(self.bot.modules.keys())[0])
        print("Debug: Bot loaded successfully!")

    def create_widgets(self):
        """Create GUI elements."""
        # File/Directory Selection
        self.path_label = tk.Label(self.root, text="Select File or Directory:")
        self.path_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.path_entry = tk.Entry(self.root, width=50)
        self.path_entry.grid(row=0, column=1, padx=10, pady=5)

        self.browse_file_button = tk.Button(self.root, text="Browse File", command=self.browse_file)
        self.browse_file_button.grid(row=0, column=2, padx=5, pady=5)

        self.browse_dir_button = tk.Button(self.root, text="Browse Directory", command=self.browse_directory)
        self.browse_dir_button.grid(row=0, column=3, padx=5, pady=5)

        # Language Selection
        self.lang_label = tk.Label(self.root, text="Language:")
        self.lang_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.lang_menu = tk.OptionMenu(self.root, self.lang_var, *list(self.bot.modules.keys()))
        self.lang_menu.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Analyze Button
        self.analyze_button = tk.Button(self.root, text="Analyze", command=self.analyze)
        self.analyze_button.grid(row=2, column=1, padx=10, pady=10)

        # Progress Bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.progress.grid(row=3, column=0, columnspan=4, padx=10, pady=5, sticky="ew")

        # Results Display
        self.result_text = tk.Text(self.root, wrap="word", height=15, width=70)
        self.result_text.grid(row=4, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        # Save Report Button
        self.save_report_button = tk.Button(self.root, text="Save Report", command=self.save_report)
        self.save_report_button.grid(row=5, column=1, pady=5)

        # Dark Mode Toggle Button
        self.dark_mode_button = tk.Button(self.root, text="Enable Dark Mode", command=self.toggle_dark_mode)
        self.dark_mode_button.grid(row=5, column=2, pady=5)

    def browse_file(self):
        """Browse and select a file."""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, file_path)

    def browse_directory(self):
        """Browse and select a directory."""
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, dir_path)

    def analyze(self):
        """Run analysis on the selected file or directory."""
        path = self.path_entry.get().strip()
        lang = self.lang_var.get()

        if not path:
            messagebox.showerror("Error", "Please select a file or directory!")
            return

        try:
            self.result_text.insert(tk.END, f"Analyzing {path} with language {lang}...\n")
            self.progress["value"] = 50
            analysis = self.bot.run(path, lang)
            self.result_text.insert(tk.END, f"Analysis completed: {analysis}\n")
            self.progress["value"] = 100
            messagebox.showinfo("Success", "Analysis completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze: {e}")
            self.progress["value"] = 0

    def save_report(self):
        """Save the analysis report to a file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                 filetypes=[("JSON files", "*.json"),
                                                            ("HTML files", "*.html")])
        if file_path:
            with open(file_path, "w") as f:
                f.write(self.result_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Report saved to {file_path}")

    def toggle_dark_mode(self):
        """Toggle between light and dark modes."""
        if self.is_dark_mode:
            self.root.configure(bg="lightgray")
            self.path_label.configure(bg="lightgray", fg="black")
            self.lang_label.configure(bg="lightgray", fg="black")
            self.result_text.configure(bg="white", fg="black")
            self.dark_mode_button.configure(text="Enable Dark Mode")
            self.is_dark_mode = False
        else:
            self.root.configure(bg="black")
            self.path_label.configure(bg="black", fg="white")
            self.lang_label.configure(bg="black", fg="white")
            self.result_text.configure(bg="black", fg="white")
            self.dark_mode_button.configure(text="Disable Dark Mode")
            self.is_dark_mode = True

    def on_close(self):
        """Handle the window close event."""
        print("Closing application...")
        self.root.destroy()


# Initialize the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = WormBotGUI(root)
    root.mainloop()
