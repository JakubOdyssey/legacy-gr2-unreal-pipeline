"""Acquire three pinned public source/notice files; compile locally with CMake.

No prebuilt reader, submodule, release executable or proprietary runtime.
Downloaded third-party files stay in ignored .local; they are not vendored.
"""
import hashlib
import os
from pathlib import Path
import subprocess
from urllib.request import Request, urlopen

COMMIT = 'fcc5d6ba444cfd3eb80677dba5e37e493941abe5'
UPSTREAM = 'https://raw.githubusercontent.com/ufbx/ufbx/' + COMMIT + '/'
# Hashes identify publicly available upstream SOURCE files, never game assets.
SOURCE_HASHES = {
    'ufbx.h':'942481725372d2ac4da5e77a062b47c20054a3440e7ee09a6043f99fe1f130ed',
    'ufbx.c':'7d8d6ae4373f71692f295ff49ee0826466306ebcaa80b0e587c13ed047b98cea',
    'LICENSE':'0dd48ebadf52273c736256325c8f078c03c8bb4facee22a4122de0ad3f615391',
}


def main():
    root = Path(__file__).resolve().parents[1]
    source = root/'.local/ufbx'; build = root/'.local/reader-build'; temporary=root/'.local/temp'
    source.mkdir(parents=True,exist_ok=True);temporary.mkdir(parents=True,exist_ok=True)
    for name,expected in SOURCE_HASHES.items():
        path=source/name
        if path.exists(): payload=path.read_bytes()
        else:
            with urlopen(Request(UPSTREAM+name,headers={'User-Agent':'legacy-neutral-source-build'}),timeout=60) as response:
                payload=response.read(2_000_001)
        if len(payload)>2_000_000 or hashlib.sha256(payload).hexdigest()!=expected:
            raise ValueError('Pinned source hash mismatch: '+name)
        path.write_bytes(payload)
    license_text=(source/'LICENSE').read_text()
    if 'Copyright (c) 2020 Samuli Raivio' not in license_text or 'ALTERNATIVE A - MIT License' not in license_text:
        raise ValueError('Unexpected upstream notice')
    env=dict(os.environ,TEMP=str(temporary),TMP=str(temporary),TMPDIR=str(temporary))
    subprocess.run(['cmake','-S',str(root),'-B',str(build),'-DUFBX_SOURCE_DIR='+str(source),'-DCMAKE_BUILD_TYPE=Release'],check=True,env=env)
    subprocess.run(['cmake','--build',str(build),'--config','Release','--parallel','2'],check=True,env=env)
    executable=build/('Release/ufbx_audit.exe' if os.name=='nt' else 'ufbx_audit')
    if not executable.exists(): raise RuntimeError('Expected reader output not found')
    print(executable.relative_to(root).as_posix())


if __name__=='__main__': main()
