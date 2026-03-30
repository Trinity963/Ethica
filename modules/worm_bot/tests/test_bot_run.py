from core.bot import Bot

bot = Bot()

# Debugging: Print all attributes of the Bot object
print("Debug: Attributes of Bot object:", dir(bot))

# Check if `run` exists
if hasattr(bot, 'run') and callable(bot.run):
    print("Debug: `run` method exists and is callable")
else:
    print("Error: `run` method is missing or not callable")
