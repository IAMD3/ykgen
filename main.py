#!/usr/bin/env python3
"""
Interactive KGen - AI Story & Video Generator

This script provides an interactive interface for users to:
- Choose between VideoAgent (story generation) or PoetryAgent (Chinese poetry)
- Select video generation provider (SiliconFlow)
- Input their own custom prompts
- Generate complete video stories with AI
"""

import sys
from kgen.cli import cli

if __name__ == "__main__":
    sys.exit(cli.main())
