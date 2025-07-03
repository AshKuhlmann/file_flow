# How to Contribute

We welcome contributions!

## Development Setup

1.  Fork and clone the repository.
2.  It's recommended to use a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  Install the project in editable mode with test dependencies:
    ```bash
    pip install -e .[test]
    ```
4.  Install pre-commit hooks:
    ```bash
    pre-commit install
    ```

## Running Tests

To run the full test suite:

```bash
pytest
```
