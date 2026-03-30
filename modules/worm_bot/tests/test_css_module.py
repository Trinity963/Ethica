import unittest
from modules.css_module import CSSModule

class TestCSSModule(unittest.TestCase):
    def setUp(self):
        # Initialize the CSS module before each test
        self.module = CSSModule()

    def test_analyze_code(self):
        # Test analysis of CSS code
        code = "body { color: red; }"
        analysis = self.module.analyze_code(code)
        self.assertIn("Avoid using 'color: red;' - consider a more accessible color.", analysis["issues"])

    def test_fix_code(self):
        # Test fixing of CSS code
        code = "body { color: red; }"
        fixed_code = self.module.fix_code(code)
        self.assertEqual(fixed_code, "body { color: #ff0000; }")

if __name__ == "__main__":
    unittest.main()
