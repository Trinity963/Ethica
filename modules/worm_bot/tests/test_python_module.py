from modules.python_module import PythonModule

try:
    module = PythonModule()
    print("PythonModule instantiated successfully!")
    print("Analyze Code Example:", module.analyze_code("print('Hello')"))
    print("Fix Code Example:", module.fix_code("print('Hello')"))
except TypeError as e:
    print(f"Error: {e}")
from modules.python_module import PythonModule

try:
    module = PythonModule()
    print("PythonModule instantiated successfully!")
    print("Analyze Code Example:", module.analyze_code("print('Hello')"))
    print("Fix Code Example:", module.fix_code("print('Hello')"))
except TypeError as e:
    print(f"Error: {e}")
