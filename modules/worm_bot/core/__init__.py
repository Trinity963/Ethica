
class Bot:
    def __init__(self):
        self.modules = {
            "python": PythonModule(),
            "css": CSSModule(),
            "javascript": JSModule(),
            "rust": RustModule(),
            "html": HTMLModule(),  # Ensure this is registered
        }
        print(f"Debug: Current registered modules: {self.modules.keys()}")  # Debug
