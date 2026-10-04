"""Run the role against simulated API actions; no router or credentials needed."""

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROLE = Path(__file__).resolve().parents[1]
ACTION = '''
import json
import os
from pathlib import Path
from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        args = self._task.args
        state_file = Path(os.environ['L2TP_TEST_STATE'])
        state = json.loads(state_file.read_text())
        path = args['path']
        rows = state.get(path, [])
        if self._task.action.endswith('api_info'):
            result.update(changed=False, result=rows)
            return result
        if args['handle_absent_entries'] != 'ignore':
            raise AssertionError('Unrelated entries must be retained')
        if args['handle_entries_content'] != 'ignore':
            raise AssertionError('Unspecified properties must be retained')
        changed = False
        for desired in args['data']:
            existing = next((row for row in rows if row.get('name') == desired.get('name')), None)
            if existing is None:
                rows.append(dict(desired))
                changed = True
            elif any(existing.get(key) != value for key, value in desired.items()):
                existing.update(desired)
                changed = True
        state[path] = rows
        if not self._task.check_mode:
            state_file.write_text(json.dumps(state))
        result.update(changed=changed, diff={'after': args['data']})
        return result
'''


@unittest.skipUnless(shutil.which('ansible-playbook'), 'ansible-playbook is required')
class RoleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='l2tp-role-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        collection = self.root / 'collections/ansible_collections/community/routeros'
        actions = collection / 'plugins/action'
        actions.mkdir(parents=True)
        (collection / 'meta').mkdir()
        (collection / 'meta/runtime.yml').write_text(
            'action_groups:\n  api:\n    - api_info\n    - api_modify\n')
        for name in ('api_info', 'api_modify'):
            (actions / f'{name}.py').write_text(ACTION)
        self.state_file = self.root / 'state.json'
        self.initial = {
            'ip pool': [{'name': 'unrelated-pool', 'ranges': '192.0.2.2-192.0.2.9'}],
            'ppp profile': [{'name': 'default-encryption', 'builtin': True}],
            'ppp secret': [{'name': 'unrelated-user', 'password': 'existing-password'}],
            'interface l2tp-server server': [{'enabled': False, 'max-mtu': 1400}],
        }
        self.write_state(self.initial)
        self.variables = {
            'mikrotik_l2tp_api_host': 'router.example.test',
            'mikrotik_l2tp_api_username': 'api-user',
            'mikrotik_l2tp_api_password': 'api-secret-marker',
            'mikrotik_l2tp_pool_ranges': '10.77.0.10-10.77.0.20',
            'mikrotik_l2tp_local_address': '10.77.0.1',
            'mikrotik_l2tp_secret_name': 'alice',
            'mikrotik_l2tp_secret_password': 'ppp-secret-marker',
            'mikrotik_l2tp_ipsec_secret': 'ipsec-secret-marker',
        }

    def write_state(self, state):
        self.state_file.write_text(json.dumps(state))

    def state(self):
        return json.loads(self.state_file.read_text())

    def run_role(self, check=False, success=True):
        playbook = self.root / 'playbook.json'
        playbook.write_text(json.dumps([{
            'hosts': 'localhost', 'gather_facts': False,
            'vars': self.variables, 'roles': [str(ROLE)],
        }]))
        environment = dict(os.environ,
                           ANSIBLE_LOCAL_TEMP=str(self.root / 'ansible-tmp'),
                           ANSIBLE_COLLECTIONS_PATH=str(self.root / 'collections'),
                           ANSIBLE_NOCOLOR='1',
                           L2TP_TEST_STATE=str(self.state_file))
        command = ['ansible-playbook', '-i', 'localhost,', '-c', 'local',
                   str(playbook), '--diff']
        if check:
            command.append('--check')
        result = subprocess.run(command, env=environment, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=60)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        for secret in ('api-secret-marker', 'ppp-secret-marker',
                       'ipsec-secret-marker', 'existing-password'):
            self.assertNotIn(secret, result.stdout)
        return result.stdout

    def test_creation_and_second_run_idempotence(self):
        self.run_role()
        state = self.state()
        self.assertEqual(state['ip pool'][-1]['ranges'], '10.77.0.10-10.77.0.20')
        profile = state['ppp profile'][-1]
        self.assertEqual(profile['local-address'], '10.77.0.1')
        self.assertEqual(profile['remote-address'], 'l2tp-pool')
        self.assertEqual(profile['use-encryption'], 'required')
        user = state['ppp secret'][-1]
        self.assertEqual(user['profile'], 'l2tp-profile')
        self.assertEqual(user['password'], 'ppp-secret-marker')
        self.assertEqual(user['service'], 'l2tp')
        server = state['interface l2tp-server server'][0]
        self.assertTrue(server['enabled'])
        self.assertEqual(server['use-ipsec'], 'required')
        self.assertEqual(server['authentication'], 'mschap2')
        self.assertFalse(server['allow-fast-path'])
        self.assertEqual(server['max-mtu'], 1400)
        for path in ('ip pool', 'ppp profile', 'ppp secret'):
            self.assertEqual(state[path][0], self.initial[path][0])
        self.assertRegex(self.run_role(), r'changed=0\s')
        self.assertEqual(self.state(), state)

    def test_existing_resources_are_preserved_even_with_different_settings(self):
        self.run_role()
        state = self.state()
        self.variables.update(mikrotik_l2tp_pool_ranges='10.88.0.10-10.88.0.20',
                              mikrotik_l2tp_secret_password='replacement-password',
                              mikrotik_l2tp_local_address='10.88.0.1')
        self.assertRegex(self.run_role(), r'changed=0\s')
        self.assertEqual(self.state(), state)

    def test_check_mode_predicts_without_writing(self):
        self.assertRegex(self.run_role(check=True), r'changed=4\s')
        self.assertEqual(self.state(), self.initial)

    def test_invalid_addressing_fails_before_any_writes(self):
        for ranges in ('10.77.0.1-10.77.0.20', '10.77.0.30-10.77.0.10',
                       '999.0.0.1', '10.77.0.10-10.77.0.20,10.77.0.15'):
            with self.subTest(ranges=ranges):
                self.variables['mikrotik_l2tp_pool_ranges'] = ranges
                self.run_role(success=False)
                self.assertEqual(self.state(), self.initial)

    def test_missing_credentials_fail_before_any_writes(self):
        self.variables['mikrotik_l2tp_ipsec_secret'] = ''
        self.run_role(success=False)
        self.assertEqual(self.state(), self.initial)

    def test_alternate_remote_pool_must_exist(self):
        self.variables['mikrotik_l2tp_remote_address'] = 'missing-pool'
        self.run_role(success=False)
        self.assertEqual(self.state(), self.initial)
        self.variables['mikrotik_l2tp_remote_address'] = 'unrelated-pool'
        self.run_role()
        self.assertEqual(self.state()['ppp profile'][-1]['remote-address'], 'unrelated-pool')

    def test_duplicate_names_fail_before_any_writes(self):
        state = copy.deepcopy(self.initial)
        state['ppp secret'].extend([{'name': 'alice'}, {'name': 'alice'}])
        self.write_state(state)
        self.run_role(success=False)
        self.assertEqual(self.state(), state)

    def test_builtin_profile_is_reused(self):
        self.variables['mikrotik_l2tp_profile_name'] = 'default-encryption'
        self.run_role()
        self.assertEqual(self.state()['ppp profile'], self.initial['ppp profile'])
        self.assertEqual(self.state()['ppp secret'][-1]['profile'], 'default-encryption')

    def test_server_settings_and_psk_are_reconciled(self):
        self.run_role()
        self.variables.update(mikrotik_l2tp_server_enabled=False,
                              mikrotik_l2tp_ipsec_secret='rotated-psk')
        self.assertRegex(self.run_role(), r'changed=1\s')
        server = self.state()['interface l2tp-server server'][0]
        self.assertFalse(server['enabled'])
        self.assertEqual(server['ipsec-secret'], 'rotated-psk')


if __name__ == '__main__':
    unittest.main()
