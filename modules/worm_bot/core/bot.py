from modules.python_module import PythonModule
from modules.css_module import CSSModule
from modules.js_module import JSModule
from modules.rust_module import RustModule
from modules.html_module import HTMLModule
from modules.json_module import JSONModule
from modules.markdown_module import MarkdownModule
import os
import importlib

# Get absolute path and ensure correct resolution to the modules directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "modules"))  # Fixing incorrect directory resolution

def load_modules(directory=MODULES_DIR):
    """Dynamically load modules from the specified directory."""
    modules = {}
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Modules directory not found: {directory}")

    for module_file in os.listdir(directory):
        if module_file.endswith(".py") and module_file != "__init__.py":
            module_name = module_file[:-3]
            try:
                module = importlib.import_module(f"modules.{module_name}")
                class_name = module_name.split("_")[0].capitalize() + "Module"
                modules[module_name.split("_")[0]] = getattr(module, class_name)()
            except Exception as e:
                print(f"Error loading module {module_name}: {str(e)}")
    
    return modules

class Bot:
    def __init__(self):
        self.modules = load_modules()

    def run(self):
        print("Bot is running with loaded modules.")
