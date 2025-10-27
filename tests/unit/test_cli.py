"""Tests for the TopDeck CLI entry point."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Dynamically determine project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
SRC_PATH = PROJECT_ROOT / "src"


class TestCLI:
    """Test suite for CLI functionality."""

    def test_help_option(self):
        """Test --help option displays help message."""
        result = subprocess.run(
            [sys.executable, "-m", "topdeck", "--help"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env={"PYTHONPATH": str(SRC_PATH)},
        )
        assert result.returncode == 0
        assert "TopDeck - Multi-Cloud Integration & Risk Analysis Platform" in result.stdout
        assert "--port" in result.stdout
        assert "--host" in result.stdout
        assert "--log-level" in result.stdout

    def test_version_option(self):
        """Test --version option displays version."""
        result = subprocess.run(
            [sys.executable, "-m", "topdeck", "--version"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env={"PYTHONPATH": str(SRC_PATH)},
        )
        assert result.returncode == 0
        assert "TopDeck v" in result.stdout
        assert "0.1.0" in result.stdout

    def test_parse_args_defaults(self):
        """Test argument parsing with defaults."""
        from topdeck.__main__ import parse_args

        with patch("sys.argv", ["topdeck"]):
            args = parse_args()
            assert args.host == "0.0.0.0"
            assert args.port == 8000
            assert args.log_level == "INFO"
            assert args.workers == 1
            assert args.reload is None
            assert args.no_reload is False

    def test_parse_args_custom_values(self):
        """Test argument parsing with custom values."""
        from topdeck.__main__ import parse_args

        with patch(
            "sys.argv",
            [
                "topdeck",
                "--host",
                "127.0.0.1",
                "--port",
                "9000",
                "--log-level",
                "DEBUG",
                "--workers",
                "4",
                "--no-reload",
            ],
        ):
            args = parse_args()
            assert args.host == "127.0.0.1"
            assert args.port == 9000
            assert args.log_level == "DEBUG"
            assert args.workers == 4
            assert args.no_reload is True

    def test_parse_args_reload_flag(self):
        """Test --reload flag."""
        from topdeck.__main__ import parse_args

        with patch("sys.argv", ["topdeck", "--reload"]):
            args = parse_args()
            assert args.reload is True
            assert args.no_reload is False

    def test_invalid_log_level(self):
        """Test invalid log level raises error."""
        result = subprocess.run(
            [sys.executable, "-m", "topdeck", "--log-level", "INVALID"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env={"PYTHONPATH": str(SRC_PATH)},
        )
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower()

    def test_invalid_port(self):
        """Test invalid port type raises error."""
        result = subprocess.run(
            [sys.executable, "-m", "topdeck", "--port", "not-a-number"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env={"PYTHONPATH": str(SRC_PATH)},
        )
        assert result.returncode != 0
        assert "invalid int value" in result.stderr.lower()
