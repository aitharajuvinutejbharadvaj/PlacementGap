import tempfile
import unittest
from pathlib import Path

from agent.graph import run_pipeline
from agent.tools.render_report import render_report


class PipelineTests(unittest.TestCase):
    def test_end_to_end_report(self):
        s = run_pipeline(
            "Used Python and SQL in a project.", "Need Python, React, and Docker skills.", 2, 4
        )
        self.assertTrue(s.gaps)
        self.assertTrue(s.trace)
        with tempfile.TemporaryDirectory() as d:
            result = render_report(s, Path(d))
            self.assertTrue(Path(result["pdf"]).read_bytes().startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
