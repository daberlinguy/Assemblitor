import sys
from pathlib import Path

from program.source.App import main

# Launcher for the main UI (Qt6).

def ver_str(ver: tuple[int, ...]):
    return ".".join([str(x) for x in ver])

min_version = (3, 10)
cur_version = sys.version_info[:3]

if cur_version < min_version:
    raise SystemExit(f"Python {ver_str(cur_version)} is not supported. Please use Python {ver_str(min_version)} or higher.")

root_dir = Path(getattr(sys, "_MEIPASS", Path.cwd()))
profile_dir = root_dir / "profile"

if __name__ == "__main__":
    main(profile_dir=profile_dir, root_dir=root_dir, dev_mode=False)
