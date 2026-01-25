#!/usr/bin/env python3

import sys
from pathlib import Path

script_dir = Path(__file__).parent
setup_script = script_dir / "scripts" / "setup_project.py"

if not setup_script.exists():
    print(f"Error: Setup script not found at {setup_script}")
    print("Please ensure .template/scripts/setup_project.py exists")
    sys.exit(1)

import subprocess
sys.exit(subprocess.call([sys.executable, str(setup_script)] + sys.argv[1:]))

