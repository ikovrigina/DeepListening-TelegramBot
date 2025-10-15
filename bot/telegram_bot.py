#!/usr/bin/env python3
import os
import sys

# Ensure parent directory is on sys.path so we can import simple_listening_bot
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from simple_listening_bot import main

if __name__ == '__main__':
    main()
