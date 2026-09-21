#!/usr/bin/python3
"""Encrypted configuration-only backup; run as root through the systemd unit."""
import json
import os
from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import tempfile

CREDENTIALS = Path('/root/.config/anansi-pve-backup')


def backup_command(snapshot_dir):
    return [
        '/usr/bin/proxmox-backup-client', 'backup',
        'etc.pxar:/etc',
        # pmxcfs is a separate FUSE mount, skipped by an /etc archive.
        'pve.pxar:/etc/pve',
        f'pve-cluster.pxar:{snapshot_dir}',
        '--backup-type', 'host',
        '--crypt-mode', 'encrypt',
        '--keyfile', str(CREDENTIALS / 'encryption-key.json'),
    ]


def snapshot_database(destination):
    # SQLite online backup API provides a consistent config.db while pmxcfs runs.
    with closing(sqlite3.connect('file:/var/lib/pve-cluster/config.db?mode=ro', uri=True)) as source:
        with closing(sqlite3.connect(str(destination))) as target:
            source.backup(target)


def main():
    os.umask(0o077)
    fstype = subprocess.check_output(
        ['/usr/bin/findmnt', '--noheadings', '--mountpoint', '/etc/pve', '--output', 'FSTYPE'],
        text=True,
    ).strip()
    if not fstype.startswith('fuse'):
        raise RuntimeError('Refusing backup: /etc/pve is not mounted as pmxcfs')
    config = json.loads((CREDENTIALS / 'repository.json').read_text())
    env = os.environ.copy()
    # Do not inherit PBS authentication overrides from an interactive environment.
    for key in list(env):
        if key.startswith('PBS_'):
            del env[key]
    env['PBS_REPOSITORY'] = config['repository']
    env['PBS_PASSWORD_FILE'] = str(CREDENTIALS / 'token')
    env['PBS_ENCRYPTION_PASSWORD_FILE'] = str(CREDENTIALS / 'key-password')
    if config['fingerprint']:
        env['PBS_FINGERPRINT'] = config['fingerprint']
    with tempfile.TemporaryDirectory(prefix='anansi-pve-backup-', dir='/run') as staging:
        snapshot_database(Path(staging) / 'config.db')
        subprocess.run(backup_command(staging), env=env, check=True, stdin=subprocess.DEVNULL)


if __name__ == '__main__':
    main()
