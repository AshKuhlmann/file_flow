# Contributing

Thank you for considering contributing to File-Flow.

## Development setup

Install the development dependencies and set up the git hooks:

```bash
pip install -r requirements.txt  # or `poetry install`
pre-commit install
```

## Docstring style

This project uses the **Google Python Style** for all docstrings. Each public
module, class and function should include a clear docstring describing its
purpose, arguments, return values and possible exceptions. The formatting is
checked automatically using `pydocstyle` via pre-commit hooks.
