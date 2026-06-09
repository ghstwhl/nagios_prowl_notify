#!/usr/bin/env python3
"""
Nagios notification script using the ProwlApp API.
Replaces the default email notification commands.

The Prowl API key should be stored in the Nagios contact's 'pager' field
($CONTACTPAGER$), as it is not used for its original purpose here.

Add the following to your Nagios commands.cfg:

  define command {
    command_name  notify-host-by-prowl
    command_line  /usr/local/bin/nagios_prowl_notify.py host \
                    --apikey $CONTACTPAGER$ \
                    --notificationtype "$NOTIFICATIONTYPE$" \
                    --hostname "$HOSTNAME$" \
                    --hoststate "$HOSTSTATE$" \
                    --hostaddress "$HOSTADDRESS$" \
                    --hostoutput "$HOSTOUTPUT$" \
                    --datetime "$LONGDATETIME$"
  }

  define command {
    command_name  notify-service-by-prowl
    command_line  /usr/local/bin/nagios_prowl_notify.py service \
                    --apikey $CONTACTPAGER$ \
                    --notificationtype "$NOTIFICATIONTYPE$" \
                    --servicedesc "$SERVICEDESC$" \
                    --hostalias "$HOSTALIAS$" \
                    --hostaddress "$HOSTADDRESS$" \
                    --servicestate "$SERVICESTATE$" \
                    --datetime "$LONGDATETIME$" \
                    --serviceoutput "$SERVICEOUTPUT$"
  }
"""

import argparse
import sys
import urllib.request
import urllib.parse
import urllib.error

PROWL_API_URL = 'https://api.prowlapp.com/publicapi/add'
APPLICATION   = 'Nagios'

# Prowl priority scale: -2 (Very Low) to 2 (Emergency)
PRIORITY_BY_STATE = {
    'DOWN':              1,   # High
    'CRITICAL':          1,   # High
    'WARNING':           0,   # Normal
    'UNKNOWN':           0,   # Normal
    'UP':               -1,   # Low
    'OK':               -1,   # Low
}

PRIORITY_BY_NOTIFICATION_TYPE = {
    'PROBLEM':           1,   # High
    'RECOVERY':         -1,   # Low
    'ACKNOWLEDGEMENT':   0,   # Normal
    'FLAPPINGSTART':     0,   # Normal
    'FLAPPINGSTOP':     -1,   # Low
    'FLAPPINGDISABLED': -1,   # Low
    'DOWNTIMESTART':    -1,   # Low
    'DOWNTIMEEND':      -1,   # Low
    'DOWNTIMECANCELLED':-1,   # Low
}


def get_priority(notification_type, state):
    """Determine Prowl priority from state first, then notification type."""
    priority = PRIORITY_BY_STATE.get(state.upper())
    if priority is None:
        priority = PRIORITY_BY_NOTIFICATION_TYPE.get(notification_type.upper(), 0)
    return priority


def send_prowl(apikey, event, description, priority=0):
    """POST a notification to the Prowl API."""
    data = urllib.parse.urlencode({
        'apikey':      apikey,
        'application': APPLICATION,
        'event':       event,
        'description': description,
        'priority':    priority,
    }).encode('utf-8')

    req = urllib.request.Request(
        PROWL_API_URL,
        data=data,
        method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )

    try:
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                print(f'Prowl API error: HTTP {response.status}', file=sys.stderr)
                sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f'Prowl API error: {e.code} {e.reason}', file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f'Prowl connection error: {e.reason}', file=sys.stderr)
        sys.exit(1)


def build_common_args():
    """Shared argument parser used as a parent for both subcommands."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--apikey',           required=True, help='Prowl API key ($CONTACTPAGER$)')
    common.add_argument('--notificationtype', required=True, help='$NOTIFICATIONTYPE$')
    common.add_argument('--datetime',         required=True, help='$LONGDATETIME$')
    return common


def main():
    parser = argparse.ArgumentParser(
        description='Send Nagios notifications via ProwlApp',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='type')
    common = build_common_args()

    # ── host subcommand ────────────────────────────────────────────────────────
    host_parser = subparsers.add_parser('host', parents=[common],
                                        help='Send a host alert notification')
    host_parser.add_argument('--hostname',    required=True, help='$HOSTNAME$')
    host_parser.add_argument('--hoststate',   required=True, help='$HOSTSTATE$')
    host_parser.add_argument('--hostaddress', required=True, help='$HOSTADDRESS$')
    host_parser.add_argument('--hostoutput',  required=True, help='$HOSTOUTPUT$')

    # ── service subcommand ─────────────────────────────────────────────────────
    svc_parser = subparsers.add_parser('service', parents=[common],
                                       help='Send a service alert notification')
    svc_parser.add_argument('--servicedesc',   required=True, help='$SERVICEDESC$')
    svc_parser.add_argument('--hostalias',     required=True, help='$HOSTALIAS$')
    svc_parser.add_argument('--hostaddress',   required=True, help='$HOSTADDRESS$')
    svc_parser.add_argument('--servicestate',  required=True, help='$SERVICESTATE$')
    svc_parser.add_argument('--serviceoutput', required=True, help='$SERVICEOUTPUT$')

    args = parser.parse_args()

    if args.type is None:
        parser.print_usage(sys.stderr)
        sys.exit(2)

    if args.type == 'host':
        event = (
            f'** {args.notificationtype} Host Alert: '
            f'{args.hostname} is {args.hoststate} **'
        )
        description = (
            f'***** Nagios *****\n\n'
            f'Notification Type: {args.notificationtype}\n'
            f'Host: {args.hostname}\n'
            f'State: {args.hoststate}\n'
            f'Address: {args.hostaddress}\n'
            f'Info: {args.hostoutput}\n\n'
            f'Date/Time: {args.datetime}'
        )
        priority = get_priority(args.notificationtype, args.hoststate)

    else:  # service
        event = (
            f'** {args.notificationtype} Service Alert: '
            f'{args.hostalias}/{args.servicedesc} is {args.servicestate} **'
        )
        description = (
            f'***** Nagios *****\n\n'
            f'Notification Type: {args.notificationtype}\n\n'
            f'Service: {args.servicedesc}\n'
            f'Host: {args.hostalias}\n'
            f'Address: {args.hostaddress}\n'
            f'State: {args.servicestate}\n\n'
            f'Date/Time: {args.datetime}\n\n'
            f'Additional Info:\n\n{args.serviceoutput}'
        )
        priority = get_priority(args.notificationtype, args.servicestate)

    send_prowl(args.apikey, event, description, priority)


if __name__ == '__main__':
    main()
