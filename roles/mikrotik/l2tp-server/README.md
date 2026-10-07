# MikroTik L2TP server

Creates an IPv4 pool, PPP profile, and one L2TP PPP user **only if their names
do not already exist**, then enables/configures the router's single L2TP server.
The server requires IPsec, uses MSCHAPv2 authentication, and disables fast path.
New PPP profiles require encryption. Unrelated entries are retained.

## Requirements

- Ansible Core 2.15 or newer and RouterOS 6.49.x or 7.x. Verify against your
  RouterOS release before production use; this role has no live-router test coverage.
- Install the collection and Python dependency on the controller, using the
  same Python environment that runs `ansible-playbook`:

  ```sh
  ansible-galaxy collection install -r roles/mikrotik/l2tp-server/requirements.yml
  python3 -m pip install -r roles/mikrotik/l2tp-server/requirements.txt
  ```

- Enable `api-ssl` on the router with a certificate matching its management
  hostname. Allow the controller to reach TCP 8729. The API user needs permission
  to read/write these paths and read sensitive properties for password/PSK
  comparisons (RouterOS `api`, `read`, `write`, and `sensitive` policies).
- Use a client pool that does not overlap LAN/DHCP networks or other VPN pools.
  The local PPP address must be outside the pool.

## Example

Inventory (`inventory.yml`):

```yaml
all:
  children:
    mikrotik:
      hosts:
        router01:
          ansible_host: router01.example.net
          ansible_connection: local
          ansible_user: ansible-vpn
          ansible_password: "{{ vault_router_api_password }}"
```

Playbook at the repository root (`l2tp.yml`):

```yaml
---
- name: Configure L2TP VPN
  hosts: mikrotik
  gather_facts: false
  become: false
  vars_files:
    - vault.yml
  vars:
    mikrotik_l2tp_pool_name: vpn-clients
    mikrotik_l2tp_pool_ranges: 10.77.0.10-10.77.0.100
    mikrotik_l2tp_profile_name: vpn-profile
    mikrotik_l2tp_local_address: 10.77.0.1
    # Defaults to the pool name; can also be one IPv4 address or another existing pool.
    mikrotik_l2tp_remote_address: "{{ mikrotik_l2tp_pool_name }}"
    mikrotik_l2tp_secret_name: alice
    mikrotik_l2tp_secret_password: "{{ vault_l2tp_password }}"
    mikrotik_l2tp_ipsec_secret: "{{ vault_l2tp_ipsec_secret }}"
    mikrotik_l2tp_api_ca_path: /etc/ansible/certs/router-ca.pem
  roles:
    - role: mikrotik/l2tp-server
```

Create `vault.yml` with `ansible-vault create vault.yml`, defining the three
`vault_*` secrets referenced above. Use strong, unique passwords and a strong PSK.

```sh
ansible-playbook -i inventory.yml l2tp.yml --ask-vault-pass --check --diff
ansible-playbook -i inventory.yml l2tp.yml --ask-vault-pass
```

## Variables

| Variable prefix: `mikrotik_l2tp_` | Default | Purpose |
| --- | --- | --- |
| `api_host` | `ansible_host` or inventory hostname | Router management address |
| `api_username` | `ansible_user` | API login; required |
| `api_password` | `ansible_password` | API password; required |
| `api_tls` | `true` | Use API TLS |
| `api_port` | `8729` with TLS, otherwise `8728` | API port |
| `api_validate_certs` | `true` | Validate certificate chain |
| `api_validate_cert_hostname` | `true` | Validate certificate hostname |
| `api_ca_path` | empty | Optional controller-side CA PEM path |
| `api_timeout` | `30` | API timeout in seconds |
| `pool_name` | `l2tp-pool` | Pool to create if missing |
| `pool_ranges` | empty; required | Comma-separated IPv4 addresses/start-end ranges |
| `profile_name` | `l2tp-profile` | PPP profile to create if missing |
| `local_address` | empty; required | Router-side PPP IPv4 address |
| `remote_address` | Pool name | Client IPv4 address or pool name |
| `secret_name` | empty; required | PPP username |
| `secret_password` | empty; required | PPP password on creation |
| `ipsec_secret` | empty; required | Server IPsec pre-shared key |
| `server_enabled` | `true` | Desired server enabled state |

All required variables must be supplied even when resources already exist.
Credentials and credential-bearing reads/writes are hidden with `no_log`;
secret writes also disable diff output.

## Existing resources and repeated runs

An existing pool/profile/user is reused as-is. Changing its variables does not
update it, rotate its password, enable a disabled user, or reassign its profile.
Check an existing user's profile/service and any per-user address overrides before
reusing it. Built-in profiles are recognized and preserved. Duplicate matching
names stop the role before any writes.

Server settings are always reconciled, including the default profile and PSK;
this affects the shared L2TP service and can affect existing VPN clients.
With readable sensitive fields, a second run with unchanged variables should
report no changes. Check mode reads the router and predicts changes without
writing; dependent creations are predictions, so it cannot prove connectivity.
API operations are sequential, without transaction rollback. After a failure,
correct the cause and rerun. Avoid concurrent runs targeting the same router.

## Firewall, routing, and client verification

Firewall/NAT changes depend on your network and must be configured separately:

- Allow inbound UDP 500/4500 and IPsec ESP as needed on the WAN interface.
- Allow UDP 1701 only when protected by inbound IPsec policy, before input drops.
- Permit the intended VPN-to-LAN forwarding, configure return routes, and add
  source NAT if VPN clients need internet access through this router.
- Ensure DNS is reachable by clients; the role does not assign DNS servers.

Connect an L2TP/IPsec client using the router's public address, PPP username and
password, and PSK. Verify its assigned address, PPP active session, IPsec installed
SAs, and access to the intended destinations. The API management connection alone
does not verify a working VPN.

Implementation references: [Ansible RouterOS API modules](https://docs.ansible.com/projects/ansible/latest/collections/community/routeros/api_modify_module.html)
and [MikroTik L2TP/IPsec configuration](https://help.mikrotik.com/docs/spaces/ROS/pages/11993097/IPsec).

## Offline verification

Run `python3 -m unittest discover -s roles/mikrotik/l2tp-server/tests -v` from
the repository root. Requires `ansible-playbook` on PATH. These tests run the real
role with simulated API action plugins to verify orchestration, preservation,
idempotence, check mode, input rejection, and credential redaction. They do not
simulate RouterOS networking or validate the API modules against a real router.
