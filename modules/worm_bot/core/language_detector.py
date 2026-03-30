import os

def detect_language(file_path):
    """Detects the programming language based on the file extension."""
    extensions = {
        ".py": "python",
        ".js": "javascript",
        ".css": "css",
        ".rs": "rust",
    }
    _, ext = os.path.splitext(file_path)
    return extensions.get(ext, "unknown")
