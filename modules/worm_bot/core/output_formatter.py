class OutputFormatter:
    @staticmethod
    def save_file(file_path, content):
        """Writes content to a file."""
        with open(file_path, 'w') as f:
            f.write(content)

    @staticmethod
    def print_to_terminal(content):
        """Displays content in the terminal."""
        print(content)

