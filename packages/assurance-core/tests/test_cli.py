import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
SCENARIO = (
    REPO_ROOT
    / "packages/assurance-contracts/scenarios/expired-consent-handover.v2.json"
)


def call(*args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(CORE_ROOT / "src")}
    return subprocess.run(
        [sys.executable, "-m", "biophysical_assurance.cli", *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class CliTests(unittest.TestCase):
    def test_authenticated_run_verify_and_report_tamper(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            key = path / "key.bin"
            key.write_bytes(b"test-only-authentication-key-32bytes!")
            bundle = path / "bundle"
            result = call(
                "run",
                str(SCENARIO),
                "--out",
                str(bundle),
                "--auth-key-file",
                str(key),
                "--key-id",
                "test",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((bundle / "auth.json").exists())
            result = call(
                "verify", str(SCENARIO), str(bundle), "--auth-key-file", str(key)
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("valid evidence", result.stdout)
            self.assertNotEqual(
                call("verify", str(SCENARIO), str(bundle)).returncode, 0
            )
            report_file = bundle / "report.json"
            report = json.loads(report_file.read_text())
            report["pass"] = False
            report_file.write_text(json.dumps(report))
            result = call(
                "verify", str(SCENARIO), str(bundle), "--auth-key-file", str(key)
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("invalid evidence", result.stdout)

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = Path(temp) / "bundle"
            self.assertEqual(
                call("run", str(SCENARIO), "--out", str(bundle)).returncode, 0
            )
            original = (bundle / "report.json").read_bytes()
            self.assertNotEqual(
                call("run", str(SCENARIO), "--out", str(bundle)).returncode, 0
            )
            self.assertEqual((bundle / "report.json").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
