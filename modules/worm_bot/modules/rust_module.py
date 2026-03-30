from base_module import BaseModule

class RustModule(BaseModule):
    def analyze_code(self, code: str) -> dict:
        """Analyzes Rust code for common issues."""
        issues = []
        if "unsafe {" in code:
            issues.append("Avoid using unsafe blocks unless absolutely necessary.")
        if "fn " not in code:
            issues.append("Missing function definition - consider adding at least one `fn`.")
        if "let _" in code:
            issues.append("Unused variable detected - consider removing it.")
        return {"issues": issues}

    def fix_code(self, code: str) -> str:
        """Fixes basic Rust code issues."""
        # Example: Add `fn main()` if missing
        if "fn main()" not in code:
            fixed_code = "fn main() {\n    // TODO: Implement main function\n}\n\n" + code
        else:
            fixed_code = code
        return fixed_code
