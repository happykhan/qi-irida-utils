#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `qi_irida_utils` package."""

import pytest
from click.testing import CliRunner
import sys
import os
my_path = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(my_path, '..'))
print(sys.path)
from qi_irida_utils.cli import cli

@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    help_result = runner.invoke(cli, ['--help'])
    assert help_result.exit_code == 0
    assert 'Show this message and exit.' in help_result.output

def test_connection():
    """Assumes localhost, tests Oauth"""
