"""Validate the IPv4 pool before making any RouterOS changes."""

from ipaddress import IPv4Address

from ansible.errors import AnsibleFilterError


def validate_addresses(ranges, local_address, remote_address, pool_name):
    try:
        local = IPv4Address(local_address)
        intervals = []
        for entry in ranges.split(','):
            ends = entry.strip().split('-')
            if len(ends) not in (1, 2):
                raise ValueError('Invalid pool range')
            start = IPv4Address(ends[0].strip())
            end = IPv4Address(ends[-1].strip())
            if start > end:
                raise ValueError('Pool range start exceeds its end')
            if start <= local <= end:
                raise ValueError('Local address must be outside the client pool')
            if any(start <= previous_end and end >= previous_start
                   for previous_start, previous_end in intervals):
                raise ValueError('Pool ranges must not overlap')
            intervals.append((start, end))
        if remote_address != pool_name:
            # An alternate existing pool name is also accepted by RouterOS.
            try:
                remote = IPv4Address(remote_address)
            except ValueError:
                if all(character in '0123456789.' for character in remote_address):
                    raise ValueError('Invalid remote IPv4 address') from None
            else:
                if remote == local:
                    raise ValueError('Local and remote addresses must differ')
        return True
    except (ValueError, TypeError, AttributeError) as error:
        raise AnsibleFilterError(f'Invalid L2TP addressing: {error}') from error


class FilterModule:
    def filters(self):
        return {'mikrotik_l2tp_validate_addresses': validate_addresses}
