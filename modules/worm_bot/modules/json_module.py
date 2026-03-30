from base_module import BaseModule
import json
import re

class JSONModule(BaseModule):
    def analyze_code(self, code: str) -> dict:
        """Analyzes JSON for syntax errors and style issues."""
        issues = []
        try:
            parsed = json.loads(code)
        except json.JSONDecodeError as e:
            issues.append(f"JSON syntax error: {e}")
            return {"issues": issues}

        # Check formatting
        formatted = json.dumps(parsed, indent=4, sort_keys=True)
        if code.strip() != formatted.strip():
            issues.append("JSON is not consistently formatted")

        return {"issues": issues}

    def fix_code(self, code: str) -> str:
        """Format JSON properly."""
        try:
            parsed = json.loads(code)
            return json.dumps(parsed, indent=4, sort_keys=True)
        except json.JSONDecodeError:
            return code
