import unittest
from modules.js_module import JSModule

class TestJSModule(unittest.TestCase):
    def setUp(self):
        self.module = JSModule()

    def test_analyze_code(self):
        code = "var name = 'John';"
        analysis = self.module.analyze_code(code)
        self.assertIn("Avoid using 'var' - use 'let' or 'const' instead.", analysis["issues"])

    def test_fix_code(self):
        code = "var name = 'John'"
        fixed_code = self.module.fix_code(code)
        self.assertEqual(fixed_code, "let name = 'John';")

if __name__ == "__main__":
    unittest.main()
