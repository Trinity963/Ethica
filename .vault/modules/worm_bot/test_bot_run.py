from core.bot import Bot

bot = Bot()

if hasattr(bot, 'run') and callable(bot.run):
    print("Debug: `run` method exists and is callable")
    try:
        analysis = bot.run("example.rs", "rust")
        print(f"Debug: Analysis results: {analysis}")
    except Exception as e:
        print(f"Error during run: {e}")
else:
    print("Error: `run` method is missing or not callable")
try:
    analysis = bot.run("example.rs", "rust")
    print(f"Debug: Analysis results: {analysis}")
except Exception as e:
    print(f"Error during run: {e}")
