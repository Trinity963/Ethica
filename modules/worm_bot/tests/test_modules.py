import unittest
from modules.python_module import PythonModule

class TestPythonModule(unittest.TestCase):
    def setUp(self):
        self.module = PythonModule()

    def test_analyze_code(self):
        code = "print('Hello, World!')"
        analysis = self.module.analyze_code(code)
        self.assertIn("Found print statement - consider logging instead.", analysis["issues"])

    def test_fix_code(self):
        code = "print('Hello, World!')"
        fixed_code = self.module.fix_code(code)
        self.assertEqual(fixed_code, "logging.info('Hello, World!')")

if __name__ == "__main__":
    unittest.main()
