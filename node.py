#!/usr/bin/env python3
"""Print this machine's stable 24-hex Lunobot node identifier."""

import hashlib
import re
import subprocess
import sys
from pathlib import Path


def digest(machine_id):
    """Hash the UTF-8 ID text, ignoring surrounding whitespace/newlines."""
    value = machine_id.strip()
    if not value:
        raise ValueError("machine identifier is empty")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def identify(platform=None, linux_id_path="/etc/machine-id"):
    platform = platform or sys.platform
    if platform.startswith("win"):
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
        ) as key:
            machine_id, _ = winreg.QueryValueEx(key, "MachineGuid")
        return digest(machine_id)

    if platform == "darwin":
        output = subprocess.check_output(
            ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"], text=True
        )
        match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', output)
        if not match:
            raise RuntimeError("ioreg did not provide IOPlatformUUID")
        return digest(match.group(1))

    if platform.startswith("linux"):
        return digest(Path(linux_id_path).read_text(encoding="utf-8"))

    if "bsd" in platform or platform.startswith(("freebsd", "openbsd", "netbsd", "dragonfly")):
        machine_id = subprocess.check_output(
            ["sysctl", "-n", "kern.hostuuid"], text=True
        )
        return digest(machine_id)

    raise RuntimeError(f"unsupported platform: {platform}")


if __name__ == "__main__":
    try:
        print(identify())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"node: {error}", file=sys.stderr)
        sys.exit(1)
