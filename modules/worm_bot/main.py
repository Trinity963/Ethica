import logging
import argparse
from core.bot import Bot


def run_bot(file_path, lang):
    """Runs the bot with the given file and language."""
    bot = Bot()
    try:
        analysis = bot.run(file_path, lang)
        logging.info("\nCode analysis completed!")
        logging.info("Issues found:", analysis["issues"])
        logging.info("Your file has been updated with fixes where applicable!")
    except ValueError as e:
        logging.info(f"Error: {e}")
    except Exception as ex:
        logging.info(f"Unexpected error: {ex}")


def command_line_mode():
    """Command-line mode for running the bot."""
    parser = argparse.ArgumentParser(description="WormBot: A modular bot for fixing code.")
    parser.add_argument("--file", type=str, help="Path to the source code file.")
    parser.add_argument("--lang", type=str, help="Specify the programming language (optional).")
    parser.add_argument("--dir", type=str, help="Path to a directory containing multiple files.")
    args = parser.parse_args()

    bot = Bot()

    if args.dir:
        # Analyze all supported files in the directory
        import os
        for root, _, files in os.walk(args.dir):
            for file in files:
                if file.endswith((".py", ".json", ".md")):  # Add supported extensions
                    full_path = os.path.join(root, file)
                    logging.info(f"Analyzing {full_path}")
                    try:
                        analysis = bot.run(full_path, args.lang)
                        logging.info(f"Issues found in {full_path}: {analysis['issues']}")
                    except Exception as e:
                        logging.info(f"Error analyzing {full_path}: {e}")
    elif args.file and args.lang:
        run_bot(args.file, args.lang)
    else:
        logging.info("Error: Either --file and --lang or --dir must be provided.")


def main():
    """Main entry point for the script."""
    command_line_mode()


if __name__ == "__main__":
    main()
