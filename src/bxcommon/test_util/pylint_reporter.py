import os
import re

from pylint import lint
from pylint.reporters.text import TextReporter

MIN_PYLINT_SCORE = 9.5
ENV_PYLINTRC_PATH = "PYLINTRC_PATH"

pylintrc_path = os.environ.get(ENV_PYLINTRC_PATH, None)

if not pylintrc_path:
    raise EnvironmentError("Specify a pylint rc file path. "
                           "Example:\n %s=/my/dir/pylintrc python -m unittest..."
                           % ENV_PYLINTRC_PATH)


def lint_directory(directory_path):
    pylint_args = [
        "-r",
        "n",
        "--msg-template={path}:{line}: [{msg_id}({symbol}), {obj}] {msg}",
        "--rcfile=" + pylintrc_path
    ]

    pylint_output = _PyLintWritable()

    lint.Run([directory_path] + pylint_args, reporter=TextReporter(pylint_output), exit=False)

    output = list(pylint_output.read())

    rate = 0
    if output:
        match = re.match(r'[^\d]+(-?\d{1,3}\.\d{2}).*', output[-3])
        if not match:
            return 0
        rate = float(match.groups()[0])

    print "".join(output)

    return rate


class _PyLintWritable(object):
    def __init__(self):
        self.content = []

    def write(self, str_content):
        self.content.append(str_content)

    def read(self):
        return self.content
