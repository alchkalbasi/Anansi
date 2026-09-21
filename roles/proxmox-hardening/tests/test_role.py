#!/usr/bin/env python3
"""Local regression checks; never connects to a PVE/PBS host."""
from contextlib import closing
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import jinja2
import yaml

ROLE = Path(__file__).resolve().parents[1]
DEFAULTS = yaml.safe_load((ROLE / 'defaults/main.yml').read_text())
spec = importlib.util.spec_from_file_location('backup_host', ROLE / 'files/backup-host.py')
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


class RoleTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('ansible-playbook'), 'Ansible not installed')
    def test_native_ansible_validation_and_rejection(self):
        # Execute only validation tasks locally, without gathering or modifying host state.
        tasks = yaml.safe_load((ROLE / 'tasks/preflight.yml').read_text())
        tasks = tasks[next(i for i, task in enumerate(tasks)
                           if task['name'] == 'Validate strict boolean switches'):]
        cases = [
            ({}, True),
            ({'pve_hardening_fail2ban': True,
              'pve_hardening_trusted_networks': ['192.0.2.0/24', '2001:db8::1'],
              'pve_hardening_journald': True,
              'pve_hardening_disable_ksm': True,
              'pve_hardening_remote_logging': True,
              'pve_hardening_log_server': 'logs.example.com',
              'pve_hardening_log_peer': 'logs.example.com',
              'pve_hardening_backup': True,
              'pve_hardening_pbs_repository': 'backup@pbs!test@pbs.example.com:test',
              'pve_hardening_pbs_password': 'test-only',
              'pve_hardening_pbs_key': '{"test": "schema-only"}',
              'pve_hardening_pbs_key_escrowed': True}, True),
            ({'pve_hardening_microcode': 'false'}, False),
            ({'pve_hardening_sshd': 'true'}, False),
            ({'pve_hardening_sshd': True, 'ansible_connection': 'ssh'}, True),
            ({'pve_hardening_sshd': True, 'ansible_connection': 'local'}, False),
            ({'pve_hardening_sshd': True, 'ansible_connection': 'ssh',
              'pve_hardening_sshd_rollback_seconds': 120}, False),
            ({'pve_hardening_disable_ksm': True, 'pve_hardening_ksm_stop_mode': 2,
              'pve_hardening_ksm_unmerge_confirmed': False}, False),
            ({'pve_hardening_fail2ban': True,
              'pve_hardening_trusted_networks': ['0.0.0.0/0']}, False),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for overrides, success in cases:
                with self.subTest(overrides=overrides):
                    play = [{'name': 'Validate role inputs', 'hosts': 'localhost',
                             'gather_facts': False, 'connection': 'local',
                             'vars': {**DEFAULTS, **overrides,
                                      'ansible_remote_tmp': directory + '/remote'},
                             'tasks': tasks}]
                    path = Path(directory) / 'validate.yml'
                    path.write_text(yaml.safe_dump(play, sort_keys=False))
                    env = {**os.environ, 'ANSIBLE_LOCAL_TEMP': directory + '/tmp',
                           'ANSIBLE_NOCOLOR': '1'}
                    result = subprocess.run(['ansible-playbook', '-i', 'localhost,', str(path)],
                                            env=env, capture_output=True, text=True)
                    self.assertEqual(result.returncode == 0, success,
                                     result.stdout + result.stderr)

    def test_mutations_respect_boolean_switches(self):
        main = yaml.safe_load((ROLE / 'tasks/main.yml').read_text())
        for task in main:
            filename = task.get('ansible.builtin.import_tasks')
            if filename in ('preflight.yml', 'logging.yml'):
                continue
            condition = task['when']
            self.assertTrue(condition.endswith(' is sameas true'), task['name'])
            self.assertIsInstance(DEFAULTS[condition.split()[0]], bool)
        logging = yaml.safe_load((ROLE / 'tasks/logging.yml').read_text())
        for task in logging:
            self.assertTrue(task['when'].endswith(' is sameas true'))
            self.assertIsInstance(DEFAULTS[task['when'].split()[0]], bool)

    def test_ssh_candidate_preserves_proxmox_settings_and_is_idempotent(self):
        self.assertIs(DEFAULTS['pve_hardening_sshd'], False)
        spec = importlib.util.spec_from_file_location(
            'pve_transaction', ROLE / 'library/linux_hardening_transaction.py')
        transaction = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(transaction)
        directives = yaml.safe_load((ROLE / 'vars/main.yml').read_text())[
            '_pve_hardening_sshd_directives']
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'sshd_config'
            include = Path(directory) / 'vendor.conf'
            include.write_text('PasswordAuthentication yes\nChallengeResponseAuthentication yes\n')
            retained = ('Port 22\nAllowTcpForwarding yes\n'
                        'AuthorizedKeysFile /etc/pve/priv/authorized_keys\n'
                        'Match Address 192.0.2.0/24\n  PasswordAuthentication yes\n')
            root.write_text(f'Include {include}\nPermitRootLogin yes\n' + retained)
            _, candidate, _ = transaction.ssh_candidates(str(root), directives, [])
            self.assertIn('PermitRootLogin prohibit-password\n', candidate[str(root)])
            self.assertIn('AuthenticationMethods publickey\n', candidate[str(root)])
            self.assertIn(retained, candidate[str(root)])
            self.assertEqual(candidate[str(include)], '')
            for path, data in candidate.items():
                Path(path).write_text(data)
            _, again, _ = transaction.ssh_candidates(str(root), directives, [])
            self.assertEqual(candidate, again)
            if Path('/usr/sbin/sshd').exists() and shutil.which('ssh-keygen'):
                key = Path(directory) / 'host_key'
                subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '',
                                '-f', str(key)], check=True)
                root.write_text('HostKey ' + str(key) + '\n' + root.read_text())
                _, candidate, includes = transaction.ssh_candidates(str(root), directives, [])
                transaction.validate_ssh(str(root), candidate, includes, False)

    def test_every_task_has_final_tags(self):
        for directory in ('tasks', 'handlers'):
            for path in (ROLE / directory).glob('*.yml'):
                for task in yaml.safe_load(path.read_text()):
                    self.assertEqual(list(task)[-1], 'tags', f'{path}: {task["name"]}')
                    self.assertIn('proxmox-hardening', task['tags'])

    def test_templates_render_with_strict_defaults(self):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(ROLE / 'templates'),
                                 undefined=jinja2.StrictUndefined)
        for path in (ROLE / 'templates').glob('*.j2'):
            output = env.get_template(path.name).render(DEFAULTS)
            self.assertNotIn('{{', output)
        apt = env.get_template('apt-security.j2').render(DEFAULTS)
        self.assertIn('Automatic-Reboot "false"', apt)
        self.assertNotIn('label=Debian"', apt)
        self.assertIn('#clear Unattended-Upgrade::Allowed-Origins;', apt)


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.credentials = self.root / 'credentials'
        self.credentials.mkdir()
        (self.credentials / 'repository.json').write_text(json.dumps({
            'repository': 'hostbackup@pbs!node@backup.example.com:hosts',
            'fingerprint': '',
        }))
        (self.credentials / 'token').write_text('secret-token')
        (self.credentials / 'key-password').write_text('secret-key-password')
        self.addCleanup(self.temp.cleanup)

    def test_mount_has_its_own_archive_and_encryption_is_mandatory(self):
        args = backup.backup_command('/run/staging')
        self.assertIn('pve.pxar:/etc/pve', args)
        self.assertIn('etc.pxar:/etc', args)
        self.assertIn('pve-cluster.pxar:/run/staging', args)
        self.assertEqual(args[args.index('--crypt-mode') + 1], 'encrypt')
        self.assertNotIn('root.pxar:/', args)

    def test_missing_pmxcfs_prevents_backup(self):
        with patch.object(backup.subprocess, 'check_output', return_value='ext4\n'), \
                patch.object(backup.subprocess, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'pmxcfs'):
                backup.main()
            run.assert_not_called()

    def test_mount_probe_failure_prevents_backup(self):
        with patch.object(backup.subprocess, 'check_output',
                          side_effect=subprocess.CalledProcessError(1, 'findmnt')), \
                patch.object(backup.subprocess, 'run') as run:
            with self.assertRaises(subprocess.CalledProcessError):
                backup.main()
            run.assert_not_called()

    def test_backup_failure_propagates_and_staging_is_cleaned(self):
        original_temp = tempfile.TemporaryDirectory
        def private_temp(**kwargs):
            return original_temp(prefix=kwargs['prefix'], dir=self.root)
        with patch.object(backup, 'CREDENTIALS', self.credentials), \
                patch.object(backup.os, 'umask'), \
                patch.object(backup.subprocess, 'check_output', return_value='fuse\n'), \
                patch.object(backup, 'snapshot_database'), \
                patch.object(backup.tempfile, 'TemporaryDirectory', side_effect=private_temp), \
                patch.object(backup.subprocess, 'run',
                             side_effect=subprocess.CalledProcessError(1, 'pbs')) as run, \
                patch.dict(os.environ, {'PBS_PASSWORD_CMD': 'untrusted-command',
                                        'PBS_PASSWORD': 'inherited-secret'}):
            with self.assertRaises(subprocess.CalledProcessError):
                backup.main()
            args, kwargs = run.call_args
            self.assertTrue(kwargs['check'])
            self.assertEqual(kwargs['stdin'], subprocess.DEVNULL)
            env = kwargs['env']
            self.assertNotIn('PBS_PASSWORD', env)
            self.assertNotIn('PBS_PASSWORD_CMD', env)
            self.assertNotIn('PBS_FINGERPRINT', env)
            self.assertEqual(env['PBS_PASSWORD_FILE'], str(self.credentials / 'token'))
            self.assertNotIn('secret-token', str(args))
            self.assertNotIn('secret-key-password', str(args))
        self.assertEqual(list(self.root.glob('anansi-pve-backup-*')), [])

    def test_sqlite_online_snapshot_preserves_committed_database(self):
        source = self.root / 'live.db'
        destination = self.root / 'config.db'
        connect = sqlite3.connect
        with closing(connect(source)) as connection:
            connection.execute('PRAGMA journal_mode=WAL')
            connection.execute('CREATE TABLE config (value TEXT)')
            connection.execute("INSERT INTO config VALUES ('committed')")
            connection.commit()
            def local_connect(name, **kwargs):
                if name == 'file:/var/lib/pve-cluster/config.db?mode=ro':
                    name = f'file:{source}?mode=ro'
                return connect(name, **kwargs)
            with patch.object(backup.sqlite3, 'connect', side_effect=local_connect):
                backup.snapshot_database(destination)
        with closing(connect(destination)) as restored:
            self.assertEqual(restored.execute('SELECT * FROM config').fetchall(), [('committed',)])
            self.assertEqual(restored.execute('PRAGMA integrity_check').fetchone(), ('ok',))


if __name__ == '__main__':
    unittest.main()
