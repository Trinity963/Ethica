import unittest
from modules.rust_module import RustModule

class TestRustModule(unittest.TestCase):
    def setUp(self):
        self.module = RustModule()

    def test_analyze_code(self):
        code = "unsafe { println!(\"This is unsafe!\"); }"
        analysis = self.module.analyze_code(code)
        self.assertIn("Avoid using unsafe blocks unless absolutely necessary.", analysis["issues"])

    def test_fix_code(self):
        code = "unsafe { println!(\"This is unsafe!\"); }"
        fixed_code = self.module.fix_code(code)
        self.assertIn("fn main()", fixed_code)

if __name__ == "__main__":
    unittest.main()
