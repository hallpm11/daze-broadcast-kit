"""Assemble the complete Windows ZIP after PyInstaller compiled the exe on Windows."""
from __future__ import annotations
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
import zipfile


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--exe', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    exe = args.exe.resolve()
    if not exe.is_file() or not exe.name.lower().endswith('.exe'):
        ap.error('A compiled Windows DazeTelemetry.exe is required.')
    project = Path(__file__).resolve().parents[1]
    packaging = project / 'packaging'
    files = [
        ('DazeTelemetry.exe', exe),
        ('INSTALL_WINDOWS.cmd', packaging / 'INSTALL_WINDOWS.cmd'),
        ('INSTALL_WINDOWS.ps1', packaging / 'INSTALL_WINDOWS.ps1'),
        ('START_DAZE.cmd', packaging / 'START_DAZE.cmd'),
        ('START_HERE.md', project / 'START_HERE.md'),
    ]
    files += [(str(f.relative_to(packaging)).replace('\\', '/'), f)
              for sub in ('assets', 'templates') for f in (packaging / sub).rglob('*') if f.is_file()]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED, compresslevel=7) as z:
        for dest, path in files:
            if not path.is_file():
                raise FileNotFoundError(f'Missing release component: {path}')
            z.write(path, 'Daze_of_Thunder_Broadcast_Kit_v1.3/' + dest)
    print(f'Built: {args.output} ({args.output.stat().st_size:,} bytes, {len(files)} entries)')


if __name__ == '__main__':
    main()
