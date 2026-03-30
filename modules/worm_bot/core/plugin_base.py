class BasePlugin:
    """Base class for all WormBot plugins."""

    def run(self, bot, file_path, **kwargs):
        """Run the plugin's functionality.
        
        Args:
            bot (Bot): Instance of the Bot class.
            file_path (str): Path to the file being analyzed.
            kwargs: Additional arguments for plugin-specific behavior.

        Returns:
            dict: A dictionary with plugin results.
        """
        raise NotImplementedError("Plugins must implement the `run` method.")
