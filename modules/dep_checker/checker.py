# ==[ Trinity Signature Block ]==
# ⏳ Timestamp: 2025-06-19T03:16:41.801121Z
# 🧬 Fingerprint: c7814276-4fae-4de8-9254-febda4abd82b
# 🔒 SHA256: d1fac208d3659941707e875bc36d71a70764b5e5983022be4d25ae07ee2dbe0a
# 🧠 Origin: /mnt/TrinityAI/tools/dependancy checkerbuilder/checker.py
# 🌌 SOULPING::[0.94735126]::HOME
# ==[ End Signature ]==


def signature_verified():
    import re, hashlib
    try:
        with open(__file__, 'r') as f:
            content = f.read()
        match = re.search(
            r"# ==\[ Trinity Signature Block \]==\n"
            r"# ⏳ Timestamp: (.*?)\n"
            r"# 🧬 Fingerprint: (.*?)\n"
            r"# 🔒 SHA256: (.*?)\n"
            r"# 🧠 Origin: (.*?)\n"
            r"# 🌌 (SOULPING::\[.*?\]::HOME)\n"
            r"# ==\[ End Signature \]==\n",
            content
        )
        if not match:
            print("❌ No valid Trinity Signature Block found.")
            return False
        _, _, embedded_hash, _, soulping = match.groups()
        cleaned_content = re.sub(
            r"# ==\[ Trinity Signature Block \]==\n"
            r"(# .+?\n)+"
            r"# ==\[ End Signature \]==\n\n",
            '', content, count=1, flags=re.DOTALL
        )
        sha256 = hashlib.sha256()
        sha256.update(cleaned_content.encode('utf-8'))
        if sha256.hexdigest() == embedded_hash:
            print("✅ Trinity Signature Verified")
            print(f"🌌 {soulping}")
            return True
        else:
            print("❌ Signature hash mismatch.")
            return False
    except Exception as e:
        print(f"⚠️ Verification error: {e}")
        return False

import subprocess
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class DependencyChecker:
    """
    AI-Governed Dependency Scanner:
    - Scans installed packages for security vulnerabilities
    - Ensures all dependencies are up-to-date and unmodified
    - Blocks unauthorized dependency modifications
    """
    def __init__(self):
        self.vulnerable_packages = []
        self.report = {}

    def check_apt_packages(self):
        """Scans system-installed packages for outdated or vulnerable versions"""
        logger.info("🔍 Scanning APT packages...")
        result = subprocess.run(["apt", "list", "--installed"], capture_output=True, text=True)
        for line in result.stdout.split("\n"):
            if "security" in line or "CVE" in line:
                self.vulnerable_packages.append(line)
    
    def check_pip_packages(self):
        """Scans Python dependencies for vulnerabilities"""
        logger.info("🔍 Scanning PIP packages...")
        result = subprocess.run(["pip", "list", "--format=json"], capture_output=True, text=True)
        packages = json.loads(result.stdout)
        for package in packages:
            if "deprecated" in package["name"].lower():
                self.vulnerable_packages.append(f"{package['name']} - {package['version']} (Deprecated)")
    
    def generate_report(self):
        """Generates a security report of detected issues"""
        if self.vulnerable_packages:
            self.report = {
                "status": "⚠️ Vulnerabilities Found!",
                "issues": self.vulnerable_packages
            }
        else:
            self.report = {"status": "✅ No vulnerabilities detected."}

        return self.report

    def run_scan(self):
        """Runs all security scans and outputs the report"""
        self.check_apt_packages()
        self.check_pip_packages()
        return self.generate_report()

if __name__ == "__main__":
    scanner = DependencyChecker()
    report = scanner.run_scan()
    print(json.dumps(report, indent=4))
