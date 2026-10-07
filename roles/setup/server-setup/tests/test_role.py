#!/usr/bin/env python3
"""Offline regressions: real Ansible assertions and native APT source parsing.

Only read-only assertions run locally. No packages, users or services are changed.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROLE = Path(__file__).resolve().parents[1]
DEFAULTS = yaml.safe_load((ROLE / 'defaults/main.yml').read_text())
FACTS = {'distribution': 'Debian', 'distribution_version': '12',
         'distribution_release': 'bookworm', 'service_mgr': 'systemd'}


def task_named(file, name):
    return next(task for task in yaml.safe_load((ROLE / 'tasks' / file).read_text())
                if task['name'] == name)


class RoleTests(unittest.TestCase):
    def run_assertions(self, overrides=None, tasks=None, expected=True):
        values = DEFAULTS | {'ansible_facts': FACTS} | (overrides or {})
        play = [{'name': 'Read-only role validation', 'hosts': 'localhost',
                 'connection': 'local', 'gather_facts': False, 'vars': values,
                 'tasks': tasks or [{'ansible.builtin.import_tasks':
                                    str(ROLE / 'tasks/preflight.yml')}]}]
        with tempfile.TemporaryDirectory(prefix='server-setup-test-') as directory:
            path = Path(directory) / 'test.yml'
            path.write_text(yaml.safe_dump(play, sort_keys=False))
            env = os.environ | {'ANSIBLE_LOCAL_TEMP': directory,
                                'ANSIBLE_NOCOLOR': '1'}
            result = subprocess.run(['ansible-playbook', '-i', 'localhost,', str(path)],
                                    env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, expected,
                         result.stdout + result.stderr)

    def test_defaults_and_non_root_automation_account(self):
        self.run_assertions({'server_setup_users': [
            {'name': 'deploy', 'sudo': True, 'passwordless_sudo': True,
             'authorized_keys': ['ssh-ed25519 AAAA example']} ]})

    def test_string_booleans_are_rejected(self):
        self.run_assertions({'server_setup_manage_apt_sources': 'false'}, expected=False)

    def test_reboot_requires_upgrade_authorization(self):
        self.run_assertions({'server_setup_allow_reboot': True}, expected=False)

    def test_passwordless_sudo_requires_a_sudo_grant(self):
        self.run_assertions({'server_setup_users': [
            {'name': 'deploy', 'passwordless_sudo': True}]}, expected=False)

    def test_duplicate_accounts_are_rejected(self):
        self.run_assertions({'server_setup_users': [
            {'name': 'deploy'}, {'name': 'deploy'}]}, expected=False)

    def test_repository_wildcards_are_rejected(self):
        self.run_assertions({'server_setup_manage_apt_sources': True,
                             'server_setup_apt_sources_to_disable': [
                                 '/etc/apt/sources.list.d/*.list']}, expected=False)

    def test_downloaded_key_repository_validation(self):
        repository = {'name': 'docker', 'url': 'https://mirror.example/docker/',
                      'key_url': 'https://mirror.example/docker/gpg',
                      'suites': ['bookworm'], 'components': ['stable'],
                      'architectures': ['amd64']}
        self.run_assertions({'server_setup_manage_apt_sources': False,
                             'server_setup_apt_repositories': [repository]})
        for changes in [{'name': '../docker'}, {'key_url': 'http://mirror.example/gpg'},
                        {'suites': 'bookworm'}, {'components': ['stable\nTrusted: yes']},
                        {'key_format': 'kbx'}]:
            with self.subTest(changes=changes):
                self.run_assertions({'server_setup_apt_repositories': [repository | changes]},
                                    expected=False)

    def test_additional_repository_native_parser_and_scoped_key(self):
        env = Environment(loader=FileSystemLoader(ROLE / 'templates'),
                          undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
        for key_format in ['asc', 'gpg']:
            repository = {'name': 'docker', 'url': 'https://mirror.example/docker/',
                          'suites': ['bookworm'], 'components': ['stable'],
                          'architectures': ['amd64', 'arm64'], 'key_format': key_format}
            rendered = env.get_template('apt-repository.sources.j2').render(item=repository)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sources') as source:
                source.write(rendered)
                source.flush()
                result = subprocess.run([
                    '/usr/bin/python3', '-c',
                    'import apt_pkg,json,sys; apt_pkg.init(); '
                    'print(json.dumps([dict(s) for s in apt_pkg.TagFile(open(sys.argv[1]))]))',
                    source.name], capture_output=True, text=True, check=True)
            stanzas = json.loads(result.stdout)
            self.assertEqual(len(stanzas), 1, rendered)
            self.assertEqual(stanzas[0]['URIs'], repository['url'])
            self.assertEqual(stanzas[0]['Suites'], 'bookworm')
            self.assertEqual(stanzas[0]['Components'], 'stable')
            self.assertEqual(stanzas[0]['Architectures'], 'amd64 arm64')
            self.assertEqual(stanzas[0]['Signed-By'],
                             '/etc/apt/keyrings/server-setup-docker.' + key_format)

    def test_afranet_mirrors_use_existing_debian_keyring(self):
        values = yaml.safe_load((ROLE.parents[2] / 'inventories/production/group_vars/afranet.yml').read_text())
        self.run_assertions(values)
        env = Environment(loader=FileSystemLoader(ROLE / 'templates'),
                          undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
        repository = {'name': 'mizban-debian',
                      'url': 'https://repo.mizbaninternal.ir/repository/debian/',
                      'suites': ['bookworm', 'bookworm-updates'],
                      'components': ['main'],
                      'signed_by': '/usr/share/keyrings/debian-archive-keyring.gpg'}
        rendered = env.get_template('apt-repository.sources.j2').render(item=repository)
        self.assertIn('Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg', rendered)
        self.run_assertions({'server_setup_apt_repositories': [repository | {
            'key_url': 'https://mirror.example/gpg'}]}, expected=False)
        self.run_assertions({'server_setup_apt_repositories': [repository | {
            'signed_by': '/tmp/untrusted.gpg'}]}, expected=False)

    def test_native_apt_parser_accepts_both_distributions_and_optional_suites(self):
        env = Environment(loader=FileSystemLoader(ROLE / 'templates'),
                          undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
        for distro, release in [('Debian', 'bookworm'), ('Ubuntu', 'noble')]:
            for optional in [False, True]:
                with self.subTest(distro=distro, optional=optional):
                    context = DEFAULTS | {
                        'ansible_facts': FACTS | {'distribution': distro,
                                                  'distribution_release': release},
                        'server_setup_apt_mirror': 'https://mirror.example/os',
                        'server_setup_apt_security_mirror': 'https://mirror.example/security',
                        'server_setup_apt_components': ['main'],
                        'server_setup_apt_source_packages': optional,
                        'server_setup_apt_backports': optional,
                        'server_setup_apt_proposed': optional}
                    rendered = env.get_template('apt.sources.j2').render(context)
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.sources') as source:
                        # TagFile is a generic deb822 parser; strip source-list
                        # comments as APT's SourceList parser does.
                        source.write('\n'.join(line for line in rendered.splitlines()
                                               if not line.startswith('#')) + '\n')
                        source.flush()
                        result = subprocess.run([
                            '/usr/bin/python3', '-c',
                            'import apt_pkg,json,sys; apt_pkg.init(); '
                            'print(json.dumps([dict(s) for s in apt_pkg.TagFile(open(sys.argv[1]))]))',
                            source.name], capture_output=True, text=True, check=True)
                    stanzas = json.loads(result.stdout)
                    self.assertEqual(len(stanzas), 2, rendered)
                    for stanza in stanzas:
                        self.assertEqual(stanza['Types'], 'deb deb-src' if optional else 'deb')
                    suites = [release, release + '-updates']
                    if optional:
                        suites += [release + '-backports', release + (
                            '-proposed-updates' if distro == 'Debian' else '-proposed')]
                    self.assertEqual(stanzas[0]['Suites'].split(), suites)
                    self.assertEqual(stanzas[0]['Components'], 'main')
                    self.assertEqual(stanzas[1]['Suites'], release + '-security')
                    self.assertIn(distro.lower() + '-archive-keyring.gpg',
                                  stanzas[0]['Signed-By'])

    def test_user_only_run_cannot_reboot_without_an_upgrade_phase(self):
        task = task_named('finish.yml', 'Reboot only when explicitly authorized')
        # Preserve the real task conditions; trip an assertion if they permit
        # a reboot after the caller selected only user/system tasks.
        task.pop('ansible.builtin.reboot')
        task['ansible.builtin.assert'] = {'that': False}
        self.run_assertions({'server_setup_upgrade_packages': True,
                             'server_setup_allow_reboot': True,
                             'server_setup_reboot_required': {'stat': {'exists': True}}},
                            tasks=[task])


if __name__ == '__main__':
    unittest.main(verbosity=2)
