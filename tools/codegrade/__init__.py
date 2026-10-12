"""codegrade: a strict code-quality grader for JavaScript, TypeScript and Python.

JavaScript and TypeScript are parsed with tree-sitter, Python with the standard ``ast`` module.
Input that isn't code in a supported language is rejected instead of scored. Code quality is a
score from 0 to 100; the Excellent / Good / Poor rank is only given to a fully reviewed
assignment (task fit, code quality and explanation).

Run it with ``python -m tools.codegrade [paths...]``.
"""

__version__ = "3.0.0"
