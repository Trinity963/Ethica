class InputHandler:
    @staticmethod
    def read_file(file_path):
        """Reads the contents of a file."""
        with open(file_path, 'r') as f:
            return f.read()

    @staticmethod
    def read_string(input_string):
        """Processes a string input."""
        return input_string
