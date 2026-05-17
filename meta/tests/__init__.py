"""Tests for the validator package."""

import subprocess


def main() -> None:
    """Test the validator."""
    subprocess.run(
        [  # noqa: S607
            "pytest",
            "meta/tests",
            "--cov=meta/validator/src/rules",
            "--cov-report=term-missing",
        ],
        check=True,
    )


__all__ = ["main"]
