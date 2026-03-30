import os
import importlib

def load_modules(directory="modules"):
    """Dynamically load modules from the specified directory."""
    modules = {}
    for module_file in os.listdir(directory):
        if module_file.endswith(".py") and module_file != "__init__.py":
            module_name = module_file[:-3]
            try:
                print(f"Debug: Attempting to load module {module_name}...")
                module = importlib.import_module(f"{directory}.{module_name}")
                class_name = module_name.split("_")[0].capitalize() + "Module"
                modules[module_name.split("_")[0]] = getattr(module, class_name)()
                print(f"Debug: Successfully loaded {class_name} from {module_name}")
            except Exception as e:
                print(f"Error loading module {module_name}: {e}")
    return modules

print("Loaded Modules:", load_modules())
