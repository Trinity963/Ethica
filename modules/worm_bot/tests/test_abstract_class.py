from modules.python_module import PythonModule

# Instantiate PythonModule to confirm compliance with BaseModule
try:
    module = PythonModule()
    print("PythonModule instantiated successfully!")
except TypeError as e:
    print(f"Error: {e}")
