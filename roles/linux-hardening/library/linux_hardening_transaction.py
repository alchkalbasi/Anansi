#!/usr/bin/python
# SPDX-License-Identifier: Apache-2.0
"""Role-local module: validate, stage, apply with watchdog, then explicitly commit."""
import fcntl
import glob
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import uuid

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r'''
module: linux_hardening_transaction
short_description: Transactional OpenSSH and iptables updates for this role
options:
  kind: {type: str, required: true, choices: [server, client, firewall]}
  action: {type: str, default: plan, choices: [plan, apply, commit]}
  directives: {type: dict, default: {}}
  scopes: {type: list, elements: dict, default: []}
  fragments: {type: dict, default: {}}
  policies: {type: dict, default: {}}
  persistent: {type: bool, default: false}
  rollback_seconds: {type: int, default: 180}
  token: {type: str, default: ''}
author: Anansi contributors
'''
EXAMPLES = r'''
- name: Check desired SSH configuration
  linux_hardening_transaction:
    kind: server
    directives:
      PermitRootLogin: {enabled: true, value: 'no'}
'''
RETURN = r'''
token:
  description: Identifier for explicit commit after a fresh authenticated connection
  type: str
  returned: when changed and applied
'''


def run(argv, data=None):
    result = subprocess.run(argv, input=data, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('%s failed: %s' % (' '.join(argv), result.stderr.strip()))
    return result.stdout


def atomic(path, data, metadata=None):
    path = Path(path)
    old = path.stat() if path.exists() else None
    fd, tmp = tempfile.mkstemp(prefix='.linux-hardening-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        mode, uid, gid = metadata or ((old.st_mode & 0o7777, old.st_uid, old.st_gid) if old else (0o600, 0, 0))
        os.chmod(tmp, mode)
        os.chown(tmp, uid, gid)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def canonical_rules(text):
    result = []
    rules = []
    for line in text.splitlines():
        if not line or line.startswith('#'):
            continue
        line = re.sub(r'\[\d+:\d+\]', '[0:0]', line)
        chain = line.split()[1] if line.startswith('-A ') else None
        if line.startswith('-A ') and 'linux-hardening:' in line:
            # xtables normalizes option order, quoting, state order, and implicit
            # TCP/UDP matches. Compare semantics for our deliberately simple rules.
            tokens = shlex.split(line)
            groups, index = [], 2
            while index < len(tokens):
                negated = tokens[index] == '!'
                index += int(negated)
                option = tokens[index]
                index += 1
                value = tokens[index] if index < len(tokens) else ''
                index += 1
                if option == '-m' and value in ('tcp', 'udp'):
                    continue
                if option == '--log-level' and value in ('4', 'warning'):
                    continue
                if option == '--ctstate':
                    value = ','.join(sorted(value.split(',')))
                if option == '-s' and value == '::1':
                    value = '::1/128'
                groups.append((negated, option, value))
            line = json.dumps([tokens[:2], sorted(groups)])
        if chain is not None:
            rules.append((chain, line))
        else:
            # Save output groups rules by chain; fragments interleave chains.
            # Stable sorting preserves the significant order within each chain.
            result.extend(rule for _, rule in sorted(rules, key=lambda item: item[0]))
            rules.clear()
            result.append(line)
    result.extend(rule for _, rule in sorted(rules, key=lambda item: item[0]))
    return '\n'.join(result) + '\n'


EMPTY_FILTER = '*filter\n:INPUT ACCEPT [0:0]\n:FORWARD ACCEPT [0:0]\n:OUTPUT ACCEPT [0:0]\nCOMMIT\n'


def firewall_snapshot(family):
    data = run([family + '-save', '-t', 'filter'])
    # An unused iptables-nft backend can have no filter table yet. Its semantic
    # baseline is ACCEPT; retain that baseline for rollback after first creation.
    return data if any(line.startswith('*') for line in data.splitlines()) else EMPTY_FILTER


def merge_rules(snapshot, fragment, policies):
    """Only enabled fragment groups may replace their own tagged rules."""
    groups = {}
    group = None
    for line in fragment.splitlines():
        if line.startswith('# control:'):
            group = line.split(':', 1)[1]
            if not re.fullmatch('[a-z_]+', group):
                raise ValueError('Invalid firewall control identifier')
            groups[group] = []
        elif line.startswith('-A '):
            if group is None:
                raise ValueError('Untagged firewall rule')
            chain, rest = line[3:].split(' ', 1)
            groups[group].append('-A %s -m comment --comment "linux-hardening:%s" %s' % (chain, group, rest))
        elif line.strip() and not line.startswith('#'):
            raise ValueError('Unexpected firewall fragment syntax')
    lines = [re.sub(r'\[\d+:\d+\]', '[0:0]', line) for line in snapshot.splitlines()
             if line and not line.startswith('#')]
    if lines[0] != '*filter' or lines[-1] != 'COMMIT':
        raise ValueError('Expected exactly one filter table')
    selected = re.compile(r'--comment ["\']?linux-hardening:([a-z_]+)["\']?(?:\s|$)')
    kept = []
    managed = []
    for line in lines[1:-1]:
        if line.startswith(':'):
            chain = line[1:].split()[0]
            control = policies.get(chain, {})
            if control.get('enabled') is True:
                value = control['value']
                if value not in ('ACCEPT', 'DROP'):
                    raise ValueError('Built-in policies must be ACCEPT or DROP')
                line = ':%s %s [0:0]' % (chain, value)
            kept.append(line)
        else:
            match = selected.search(line)
            if match and match[1] in groups:
                continue
            if match:
                managed.append((match[1], line))
            else:
                kept.append(line)
    for name, rules in groups.items():
        managed.extend((name, line) for line in rules)
    order = ['drop_invalid', 'anti_spoofing', 'allow_loopback', 'allow_established', 'allow_ssh',
             'allow_icmp', 'custom_tcp', 'custom_udp', 'outbound_tcp', 'outbound_udp', 'log_dropped']
    managed.sort(key=lambda pair: order.index(pair[0]) if pair[0] in order else len(order))
    declarations = [line for line in kept if line.startswith(':')]
    foreign = [line for line in kept if not line.startswith(':')]
    early = [line for name, line in managed if name != 'log_dropped']
    logs = [line for name, line in managed if name == 'log_dropped']
    # Log only fallthrough packets on chains whose effective policy is DROP.
    drop_chains = {line[1:].split()[0] for line in declarations if line.split()[1] == 'DROP'}
    if 'log_dropped' in groups:
        logs = [line for line in logs if line.split()[1] in drop_chains]
    return '\n'.join(['*filter'] + declarations + early + foreign + logs + ['COMMIT']) + '\n'


def directive_lines(options):
    result = {}
    for name, control in options.items():
        if control.get('enabled') is not True:
            continue
        if not re.fullmatch('[A-Za-z][A-Za-z0-9]+', name) or name.lower() in ('include', 'match', 'host'):
            raise ValueError('Invalid directive: ' + name)
        values = control['value'] if isinstance(control['value'], list) else [control['value']]
        lines = []
        for value in values:
            if not isinstance(value, (str, int)) or not str(value).strip() or '\n' in str(value) or '\r' in str(value):
                raise ValueError('Enabled directive needs a nonempty single-line value: ' + name)
            lines.append(name + ' ' + str(value))
        result[name.lower()] = lines
    return result


def ssh_candidates(root, directives, scopes, client=False):
    """Follow local Includes; change globals only; leave disabled directives byte-for-byte."""
    selected = directive_lines(directives)
    originals, contents = {}, {}
    includes = {}
    stack = []
    scope_word = 'host' if client else 'match'

    def visit(path, global_context=True):
        path = Path(path)
        real = path.resolve()
        if not real.is_relative_to(Path(root).parent.resolve()):
            raise ValueError('SSH Include must stay within ' + str(Path(root).parent))
        if str(real) in stack or str(real) in originals:
            raise ValueError('Repeated or recursive SSH Include: ' + str(path))
        if path.is_symlink():
            raise ValueError('Manage regular SSH config files, not symlinks: ' + str(path))
        stack.append(str(real))
        original = path.read_text()
        originals[str(path)] = original
        output = []
        for line in original.splitlines(keepends=True):
            words = shlex.split(line, comments=True)
            key = words[0].lower() if words else ''
            if key in ('match', 'host'):
                global_context = client and key == 'host' and words[1:] == ['*']
            if key == 'include':
                children = []
                for pattern in words[1:]:
                    if not os.path.isabs(pattern):
                        pattern = str(Path(root).parent / pattern)
                    for child in sorted(glob.glob(pattern)):
                        global_context = visit(child, global_context)
                        children.append(child)
                includes[(str(path), line)] = children
            # ChallengeResponseAuthentication aliases KbdInteractiveAuthentication.
            alias = 'kbdinteractiveauthentication' if key == 'challengeresponseauthentication' else key
            if global_context and alias in selected:
                continue
            output.append(line)
        contents[str(path)] = ''.join(output)
        stack.pop()
        return global_context

    visit(root)
    prefix = '\n'.join(line for lines in selected.values() for line in lines)
    if prefix:
        if client:
            end = '# end linux-hardening client defaults\n'
            if end in contents[root]:
                contents[root] = contents[root].replace(end, prefix + '\n' + end)
            else:
                contents[root] = contents[root].rstrip('\n') + '\n# linux-hardening client defaults\nHost *\n' + prefix + '\n' + end
        else:
            contents[root] = prefix + '\n' + contents[root]
    for scope in reversed(scopes):
        if scope.get('enabled') is not True:
            continue
        identifier, criterion = scope['id'], scope['match']
        if not re.fullmatch('[a-z0-9_-]+', identifier) or '\n' in criterion or '\r' in criterion:
            raise ValueError('Invalid SSH scope')
        if not client and not re.match(r'^(User|Group|Address|LocalPort)\s+\S', criterion):
            raise ValueError('Match must use User, Group, Address or LocalPort')
        rules = directive_lines(scope['directives'])
        start, end = '# linux-hardening scope ' + identifier, '# end linux-hardening scope ' + identifier
        current = contents[root]
        pattern = re.compile(re.escape(start) + r'\n(.*?)' + re.escape(end) + r'\n?', re.S)
        old = pattern.search(current)
        retained = []
        if old:
            oldlines = old[1].splitlines()
            if oldlines and oldlines[0] != scope_word.title() + ' ' + criterion:
                raise ValueError('Changing a scope criterion requires explicit manual migration')
            retained = [x for x in oldlines[1:] if x.strip() and x.split()[0].lower() not in rules]
        block = start + '\n' + scope_word.title() + ' ' + criterion + '\n'
        block += '\n'.join(retained + ['  ' + x for lines in rules.values() for x in lines]) + '\n' + end + '\n'
        if old:
            contents[root] = pattern.sub(lambda _: block, current)
        elif rules:
            if client:
                # Specific Host sections precede global options, because ssh uses
                # the first obtained value. Reset the context for the original file.
                contents[root] = block + 'Host *\n' + current
                continue
            # Place before existing scopes so explicit role exceptions take precedence.
            boundary = re.search(r'(?im)^\s*(?:Match|Host)\s+', current)
            if boundary:
                contents[root] = current[:boundary.start()] + block + current[boundary.start():]
            else:
                contents[root] = current.rstrip('\n') + '\n' + block
    return originals, contents, includes


def validate_ssh(root, contents, includes, client):
    with tempfile.TemporaryDirectory(prefix='linux-hardening-ssh-') as temp:
        mapping = {path: str(Path(temp) / str(n)) for n, path in enumerate(contents)}
        for path, data in contents.items():
            for (parent, line), children in includes.items():
                if parent == path:
                    replacement = ''.join('Include ' + mapping[child] + '\n' for child in children)
                    data = data.replace(line, replacement)
            Path(mapping[path]).write_text(data)
        if client:
            run(['/usr/bin/ssh', '-G', '-F', mapping[root], 'localhost'])
        else:
            run(['/usr/sbin/sshd', '-t', '-f', mapping[root]])


# The watchdog runs independently of Ansible and survives loss of the SSH transport.
# Commit and rollback serialize on one lock; rolled-back transactions cannot be committed.
WATCHDOG = r'''
import fcntl,json,os,subprocess,sys,tempfile
from pathlib import Path
state=Path(sys.argv[1])
with (state/'lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 if not (state/'pending').exists(): sys.exit(0)
 info=json.loads((state/'state.json').read_text())
 errors=[]
 for path,record in info['files'].items():
  try:
   if record is None:
    Path(path).unlink(missing_ok=True)
    continue
   fd,tmp=tempfile.mkstemp(dir=str(Path(path).parent))
   with os.fdopen(fd,'w') as f: f.write(record['content'])
   os.chmod(tmp,record['mode']);os.chown(tmp,record['uid'],record['gid']);os.replace(tmp,path)
  except Exception as e: errors.append(str(e))
 for family,data in info['firewall'].items():
  result=subprocess.run([family+'-restore','--wait','10'],input=data,text=True,capture_output=True)
  if result.returncode: errors.append(result.stderr)
 if info['kind']=='server':
  result=subprocess.run(['/usr/sbin/sshd','-t'],capture_output=True)
  if result.returncode==0:
   result=subprocess.run(['systemctl','reload','ssh.service'],capture_output=True)
  if result.returncode: errors.append('SSH rollback validation/reload failed')
 (state/'rolled-back').write_text('\n'.join(errors) or 'restored')
 (state/'pending').unlink()
 if errors: sys.exit(1)
'''


def state_root(kind):
    return Path('/run/linux-hardening-' + kind)


def persistence_path(family):
    return Path('/etc/iptables/rules.' + ('v4' if family == 'iptables' else 'v6'))


def snapshot_files(contents):
    result = {}
    for name in contents:
        stat = Path(name).stat()
        result[name] = dict(content=Path(name).read_text(), mode=stat.st_mode & 0o7777,
                            uid=stat.st_uid, gid=stat.st_gid)
    return result


def commit(kind, token):
    state = state_root(kind)
    if not re.fullmatch('[a-f0-9]{32}', token) or not state.is_dir():
        raise ValueError('No valid pending transaction')
    with (state / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        info = json.loads((state / 'state.json').read_text())
        if info['token'] != token or not (state / 'pending').exists():
            raise ValueError('Transaction expired, rolled back, or ownership changed')
        for path, content in info['desired_files'].items():
            if Path(path).read_text() != content:
                raise ValueError('Concurrent SSH configuration change; leaving rollback armed')
        for family, desired in info['desired_firewall'].items():
            if canonical_rules(firewall_snapshot(family)) != canonical_rules(desired):
                raise ValueError('Concurrent firewall change; leaving rollback armed')
        # Stage and validate persistence before replacing any existing persistent file.
        persistent = {}
        if info['persistent']:
            for family in info['desired_firewall']:
                persistent[str(persistence_path(family))] = run([family + '-save'])
            for path, data in persistent.items():
                family = 'iptables' if path.endswith('v4') else 'ip6tables'
                run([family + '-restore', '--test', '--wait', '10'], data)
            # Extend the same rollback journal before the first persistence write.
            for path in persistent:
                info['files'].update(snapshot_files([path]) if Path(path).exists() else {path: None})
            atomic(state / 'state.json', json.dumps(info))
            for path, data in persistent.items():
                if not Path(path).exists() or canonical_rules(Path(path).read_text()) != canonical_rules(data):
                    atomic(path, data, (0o600, 0, 0))
        (state / 'pending').unlink()
    run(['systemctl', 'stop', 'linux-hardening-' + token + '.timer'])
    shutil.rmtree(state)


def apply_transaction(kind, originals, desired_files, firewall, desired_firewall, persistent, seconds):
    state = state_root(kind)
    if state.exists():
        # Never reuse stale state or disarm somebody else's watchdog.
        raise ValueError('Existing transaction state requires inspection: ' + str(state))
    state.mkdir(mode=0o700)
    token = uuid.uuid4().hex
    info = dict(kind=kind, token=token, files=snapshot_files(desired_files),
                desired_files=desired_files, firewall=firewall, desired_firewall=desired_firewall,
                persistent=persistent)
    (state / 'state.json').write_text(json.dumps(info))
    (state / 'rollback.py').write_text(WATCHDOG)
    (state / 'pending').touch()
    armed = False
    try:
        run(['systemd-run', '--quiet', '--unit=linux-hardening-' + token,
             '--on-active=' + str(seconds) + 's', '--timer-property=AccuracySec=1s',
             '/usr/bin/python3', str(state / 'rollback.py'), str(state)])
        armed = True
        with (state / 'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if not (state / 'pending').exists():
                raise ValueError('Rollback deadline passed before application')
            for path in desired_files:
                if Path(path).read_text() != originals[path]:
                    raise ValueError('Concurrent SSH configuration edit')
            for family in firewall:
                if canonical_rules(firewall_snapshot(family)) != canonical_rules(firewall[family]):
                    raise ValueError('Concurrent firewall writer detected')
            for path, data in desired_files.items():
                atomic(path, data)
            for family, data in desired_firewall.items():
                if canonical_rules(data) != canonical_rules(firewall[family]):
                    run([family + '-restore', '--wait', '10'], data)
            if kind == 'server':
                run(['/usr/sbin/sshd', '-t'])
                run(['systemctl', 'reload', 'ssh.service'])
    except Exception:
        if armed:
            subprocess.run(['/usr/bin/python3', str(state / 'rollback.py'), str(state)], check=False)
        else:
            shutil.rmtree(state)
        raise
    return token


def main():
    module = AnsibleModule(argument_spec=dict(
        kind=dict(type='str', required=True, choices=['server', 'client', 'firewall']),
        action=dict(type='str', default='plan', choices=['plan', 'apply', 'commit']),
        directives=dict(type='dict', default={}), scopes=dict(type='list', elements='dict', default=[]),
        fragments=dict(type='dict', default={}), policies=dict(type='dict', default={}),
        persistent=dict(type='bool', default=False), rollback_seconds=dict(type='int', default=180),
        token=dict(type='str', default='')), supports_check_mode=True)
    p = module.params
    try:
        if p['action'] == 'commit':
            if not module.check_mode:
                commit(p['kind'], p['token'])
            module.exit_json(changed=False)
        originals, desired, firewall, new_firewall = {}, {}, {}, {}
        if p['kind'] in ('server', 'client'):
            client = p['kind'] == 'client'
            root = '/etc/ssh/ssh_config' if client else '/etc/ssh/sshd_config'
            originals, contents, includes = ssh_candidates(root, p['directives'], p['scopes'], client)
            validate_ssh(root, contents, includes, client)
            desired = {path: data for path, data in contents.items() if data != originals[path]}
            if not client and desired:
                # Socket activation owns listeners; do not silently change ports behind it.
                socket_active = subprocess.run(['systemctl', 'is-active', '--quiet', 'ssh.socket']).returncode == 0
                listener_keys = ('port', 'listenaddress', 'addressfamily')
                if socket_active and any(k in directive_lines(p['directives']) for k in listener_keys):
                    raise ValueError('Listener changes require an operator-managed migration from ssh.socket first')
                run(['systemctl', 'is-active', '--quiet', 'ssh.service'])
        else:
            for family, fragment in p['fragments'].items():
                if family not in ('iptables', 'ip6tables'):
                    raise ValueError('Unsupported firewall family')
                firewall[family] = firewall_snapshot(family)
                new_firewall[family] = merge_rules(firewall[family], fragment, p['policies'])
                run([family + '-restore', '--test', '--wait', '10'], new_firewall[family])
        changed = bool(desired) or any(canonical_rules(data) != canonical_rules(firewall[family])
                                       for family, data in new_firewall.items())
        if p['persistent']:
            for family in new_firewall:
                path = persistence_path(family)
                saved = run([family + '-save'])
                changed = changed or not path.exists() or canonical_rules(path.read_text()) != canonical_rules(saved)
        if module.check_mode or p['action'] == 'plan' or not changed:
            module.exit_json(changed=changed)
        if p['kind'] == 'client':
            for path, data in desired.items():
                atomic(path, data)
            module.exit_json(changed=True)
        if p['rollback_seconds'] < 60:
            raise ValueError('Rollback timeout must be at least 60 seconds')
        token = apply_transaction(p['kind'], originals, desired, firewall, new_firewall,
                                  p['persistent'], p['rollback_seconds'])
        module.exit_json(changed=True, token=token)
    except (ValueError, RuntimeError, OSError, KeyError) as error:
        module.fail_json(msg=str(error))


if __name__ == '__main__':
    main()
