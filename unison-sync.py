#!/usr/bin/env python

# <bitbar.title>Unison Sync</bitbar.title>
# <bitbar.version>v0.1</bitbar.version>
# <bitbar.author>Martin Aspeli</bitbar.author>
# <bitbar.author.github>optilude</bitbar.author.github>
# <bitbar.desc>A poor man's Dropbox using unison to sync to mounted drives.</bitbar.desc>
# <bitbar.dependencies>python,unison</bitbar.dependencies>
# <bitbar.abouturl>https://github.com/optilude/unison-bitbar</bitbar.abouturl>

import re
import os
import os.path
import subprocess
import socket
import contextlib
import argparse
import urlparse

# Match config file parameters, *including* parameters in comment lines
# (our additional parameters can only be set that way to avoid upsetting unison)
CONFIG_PARAMETER = re.compile(r'^\s*#?\s*(\S+)\s*=\s*(.+?)\s*$')
FLAG_FILE = 'unison-sync.stopped'
PORTS = {
    'smb': 139,
    'afp': 548
}

def main():

    # Prepare environment

    if 'PATH' in os.environ and not '/usr/local/bin' in os.environ['PATH'] and os.path.isdir('/usr/local/bin'):
        os.environ['PATH'] += ':/usr/local/bin'

    unison_directory = os.path.join(os.environ['HOME'], '.unison')
    if not os.path.exists(unison_directory):
        os.mkdir(unison_directory)
    flag_file = os.path.join(unison_directory, FLAG_FILE)

    parser = argparse.ArgumentParser(description='Attempt to mount a file share and run Unison')
    parser.add_argument('profile', metavar='default.conf', default='default.conf', nargs='?', help='Name of Unison profile')
    parser.add_argument('--mount', dest='mount', action='store_true', help='Only mount share')
    parser.add_argument('--unmount', dest='unmount', action='store_true', help='Only unmount share')
    parser.add_argument('--stop', dest='stop', action='store_true', help='Stop syncing')
    parser.add_argument('--restart', dest='restart', action='store_true', help='Restart syncing')

    args = parser.parse_args()
    try:
        config = parse_profile(unison_directory, args.profile)
    except:
        print_error("Could not load profile %s" % args.profile)
        return

    stopped = is_stopped(flag_file)
    mounted = is_mounted(config['sync:mountpoint']) if 'sync:mountpoint' in config else True
    synced = False

    if args.mount and 'sync:mounturi' in config and not mounted:
        attempt_mount(config['sync:mounturi'])
        mounted = True
    elif args.unmount and 'sync:mountpoint' in config and mounted:
        attempt_unmount(config['sync:mountpoint'])
        mounted = False
    elif args.stop:
        stop(flag_file)
        stopped = True
    elif args.restart:
        restart(flag_file)
        stopped = False
    elif not stopped:
        # Normal run, no flags

        # If we have a URI set and we're not mounted, do that next instead
        # of syncing. We can't easily wait until the mount succeeds, so we
        # just wait until the next run
        if not mounted and 'sync:mounturi' in config:
            attempt_mount(config['sync:mounturi'])

        # Otherwise run sync, but avoid even calling unison if mountpoint isn't
        # found
        if mounted:
            synced = attempt_sync(args.profile)

    print_success(synced=synced, mounted=mounted, stopped=stopped)

def parse_profile(unison_directory, profile):
    """Load unison profile into dict
    """

    config = {}
    filename = os.path.join(unison_directory, profile)

    with open(filename) as profile_file:
        for line in profile_file:
            # parse in comments, too, because our sync: special hints can only be placed in comments

            match = CONFIG_PARAMETER.match(line)
            if match:
                name, value = match.groups()
                if name and value:
                    if name in config:
                        if isinstance(config[name], list):
                            config[name].append(value)
                        else:
                            config[name] = [config[name], value]
                    else:
                        config[name] = value

    return config

def check_socket(host, port):
    """Determine if socket is reachable (http://stackoverflow.com/questions/19196105/python-how-to-check-if-a-network-port-is-open-on-linux)
    """
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            return sock.connect_ex((host, port)) == 0
        except socket.gaierror:  # cannot reach hostname
            return False

def is_reachable(uri):
    """Determine if the server at the given URI can indeed be reached
    """

    url = urlparse.urlparse(uri)
    host = url.netloc
    port = PORTS.get(url.scheme, None)

    if '@' in host:
        host = host.partition('@')[-1]

    # TODO: This falsely succeeds when connected in non-elevated mode :-/

    return check_socket(host, port)

def is_mounted(mountpoint):
    """Determine if drive is mounted (mount point exists)
    """
    return os.path.exists(mountpoint)

def attempt_mount(uri):
    """Attempt to mount the given URI and then attempt to sync
    """

    if not is_reachable(uri):
        return False

    return subprocess.call(["open", uri]) == 0

def attempt_unmount(mountpoint):
    """Unmount the given mount point
    """

    return subprocess.call(["unmount", mountpoint]) == 0

def is_stopped(flag_file):
    """Determine if stopped marker is set
    """

    return os.path.exists(flag_file)

def stop(flag_file):
    """Set marker to indicate syncing has stopped
    """
    if not os.path.exists(flag_file):
        with open(flag_file, 'w') as f:
            f.write("stopped")

def restart(flag_file):
    """Remove stopped-sync marker
    """
    if os.path.exists(flag_file):
        os.unlink(flag_file)

def attempt_sync(profile):
    """Attempt to run unison sync
    """

    return subprocess.call(["unison", profile]) == 0

def print_error(error):
    """Print the bitbar output for an error
    """

    print ":exclamation:"
    print "---"
    print error

def print_success(synced=None, mounted=False, stopped=False):
    """Print the bitbar output for success
    """

    script = os.path.realpath(__file__)

    if stopped or not mounted:
        print ":no_entry_sign:"
    elif synced:
        print ":heavy_check_mark:"
    else:
        print ":heavy_multiplication_x:"

    print "---"

    if mounted:
        print "Unmount | refresh=true terminal=false bash=%s param1=--unmount" % script
    else:
        print "Mount | refresh=true terminal=false bash=%s param1=--mount" % script

    if stopped:
        print "Restart | refresh=true terminal=false bash=%s param1=--restart" % script
    else:
        print "Stop | refresh=true terminal=false bash=%s param1=--stop" % script

    print "Retry | refresh=true"

if __name__ == '__main__':
    main()
