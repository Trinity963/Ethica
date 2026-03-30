from abc import ABC, abstractmethod

class BaseModule(ABC):
    @abstractmethod
    def analyze_code(self, code: str) -> dict:
        """Analyze the provided code for issues."""
        pass

    @abstractmethod
    def fix_code(self, code: str) -> str:
        """Fix the identified issues in the code."""
        pass
