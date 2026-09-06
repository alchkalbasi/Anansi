#!/usr/bin/python
# SPDX-License-Identifier: Apache-2.0
"""Filter weak OpenSSH DH groups without replacing the file with an empty set."""
import os
import tempfile

from ansible.module_utils.basic import AnsibleModule


def filter_moduli(text, minimum):
    kept = []
    for line in text.splitlines(keepends=True):
        fields = line.split()
        # OpenSSH's size field is one less than the actual group size in bits.
        if not fields or line.startswith('#') or int(fields[4]) + 1 >= minimum:
            kept.append(line)
    if not any(line.strip() and not line.startswith('#') for line in kept):
        raise ValueError('No sufficiently strong moduli remain; original file retained')
    return ''.join(kept)


def main():
    module = AnsibleModule(
        argument_spec=dict(path=dict(type='path', required=True), minimum=dict(type='int', default=2048)),
        supports_check_mode=True,
    )
    temporary = None
    try:
        if module.params['minimum'] < 2048:
            raise ValueError('Hardening requires a DH minimum of at least 2048 bits')
        with open(module.params['path']) as stream:
            original = stream.read()
        filtered = filter_moduli(original, module.params['minimum'])
        if filtered != original and not module.check_mode:
            metadata = os.stat(module.params['path'])
            fd, temporary = tempfile.mkstemp(dir=os.path.dirname(module.params['path']))
            with os.fdopen(fd, 'w') as stream:
                stream.write(filtered)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, metadata.st_mode & 0o7777)
            os.chown(temporary, metadata.st_uid, metadata.st_gid)
            module.atomic_move(temporary, module.params['path'])
        module.exit_json(changed=filtered != original)
    except (ValueError, OSError, IndexError) as error:
        module.fail_json(msg=str(error))
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


if __name__ == '__main__':
    main()
