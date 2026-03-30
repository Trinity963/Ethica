from core.bot import Bot

# Initialize the bot
bot = Bot()
print(dir(bot))  # Ensure 'run' is listed in the Bot object's methods.

# Analyze a file with plugins
file_path = "example.py"
results = bot.run(file_path, lang="python")

print("\nAnalysis Results:")
print(results["analysis"])

print("\nPlugin Results:")
for plugin, result in results["plugins"].items():
    print(f"{plugin}: {result}")
from core.bot import Bot

# Initialize the bot
bot = Bot()

# User input for file and language
file_path = input("Enter the file path to analyze: ").strip()
lang = input("Enter the programming language: ").strip()

# Analyze the file
try:
    results = bot.run(file_path, lang=lang)
    
    # Print analysis results
    print("\nAnalysis Results:")
    print(results["analysis"])
    
    # Print plugin results
    print("\nPlugin Results:")
    for plugin, result in results["plugins"].items():
        print(f"{plugin}: {result}")
    
except Exception as e:
    print(f"Error during analysis: {e}")
