import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "design_gate.py"
spec = importlib.util.spec_from_file_location("design_gate", SCRIPT)
dg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dg)

class DesignGateTests(unittest.TestCase):
    def test_python_long_function_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.py"
            body = "\n".join(f"    value += {i}" for i in range(41))
            path.write_text(
                f"def too_long():\n    value = 0\n{body}\n    return value\n",
                encoding="utf-8"
            )
            issues = dg.python_function_issues(path, 40)
            self.assertTrue(any("too_long" in issue for issue in issues))

    def test_comments_not_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.py"
            comments = "\n".join("    # comment" for _ in range(50))
            path.write_text(
                f"def short():\n{comments}\n    return 1\n",
                encoding="utf-8"
            )
            self.assertEqual([], dg.python_function_issues(path, 40))

    def test_only_design_paths_allowed_before_approval(self):
        config = dict(dg.DEFAULT_CONFIG)
        self.assertTrue(
            dg.is_allowed_before_approval("docs/designs/T-1-a.md", config)
        )
        self.assertFalse(
            dg.is_allowed_before_approval("src/service.py", config)
        )

if __name__ == "__main__":
    unittest.main()
