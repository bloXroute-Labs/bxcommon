import unittest

from bxcommon.test_utils import pylint_reporter
from bxcommon.test_utils.pylint_reporter import MIN_PYLINT_SCORE


class LintTests(unittest.TestCase):
    def test_lint_score(self):
        lint_score = pylint_reporter.lint_directory("../src/bxcommon")

        self.assertGreater(lint_score, MIN_PYLINT_SCORE, "Lint score was too low, please lint and refactor your code.")
