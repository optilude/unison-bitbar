#!/usr/bin/env python

import os
import os.path
import subprocess
import socket
import contextlib
import argparse
import urlparse

FLAG_FILE = os.path.join('/', 'tmp', 'unison-sync.stopped')
PORTS = {
    'smb': 139,
    'afp': 548
}

def main():
        
    parser = argparse.ArgumentParser(description='Attempt to mount a file share and run Unison')
    parser.add_argument('profile', metavar='default.conf', default='default.conf', help='Name of Unison profile')
    parser.add_argument('--mount', dest='mount', action='store_true', help='Only mount share')
    parser.add_argument('--unmount', dest='unmount', action='store_true', help='Only unmount share')
    parser.add_argument('--stop', dest='stop', action='store_true', help='Stop syncing')
    parser.add_argument('--restart', dest='restart', action='store_true', help='Restart syncing')
    
    args = parser.parse_args()
    try:
        config = parse_profile(args.profile)
    except:
        print_error("Could not load profile %s" % args.profile)
        return
    
    stopped = is_stopped()
    mounted = is_mounted(config['mountpoint']) if 'mountpoint' in config else False
    
    if args.mount and 'uri' in config:
        mounted = attempt_mount(config['uri'])
        print_success(mounted=mounted, stopped=stopped)
    elif args.unmount and 'mountpoint' in config:
        attempt_unmount(config['mountpoint'])
        print_success(mounted=False, stopped=stopped)
    elif args.stop:
        stop()
        print_success(mounted=mounted, stopped=True)
    elif args.restart:
        restart()
        print_success(mounted=mounted, stopped=False)
    else:
        synced = None
        if not stopped:
            if not mounted and 'uri' in config:
                mounted = attempt_mount(config['uri'])
            synced = attempt_sync(args.profile)

        print_success(synced=synced, mounted=mounted, stopped=stopped)

def parse_profile(profile):
    """Load unison profile into dict
    """
    
    config = {}
    filename = os.path.join(os.environ['HOME'], '.unison', profile)
    
    with open(filename) as profile_file:
        for line in profile_file:
            name, value = line.partition("=")[::2]
            name = name.strip()
            value = value.strip()
            if name and value:
                if value.startswith('"') and value.endswith('"'):
                    value = value.strip('"')
                if value.startswith("'") and value.endswith("'"):
                    value = value.strip("'")
            
                config[name] = value
    
    return config

def check_socket(host, port):
    """Determine if socket is reachable (http://stackoverflow.com/questions/19196105/python-how-to-check-if-a-network-port-is-open-on-linux)
    """
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        return sock.connect_ex((host, port)) == 0

def is_reachable(uri):
    """Determine if the server at the given URI can indeed be reached
    """
    
    url = urlparse.urlparse(uri)
    host = url.netloc
    port = PORTS.get(url.scheme, None)
    
    if '@' in host:
        host = netloc.partition('@')[-1]
    
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

def is_stopped():
    """Determine if stopped marker is set
    """
    
    return os.path.exists(FLAG_FILE)

def stop():
    """Set marker to indicate syncing has stopped
    """
    
    if not os.path.exists(FLAG_FILE):
        os.mknod(FLAG_FILE)
    
def restart():
    """Remove stopped-sync marker
    """
    
    if os.path.exists(FLAG_FILE):
        os.unlink(FLAG_FILE)

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

def print_success(success=None, mounted=False, stopped=False):
    """Print the bitbar output for success
    """
    
    if success == True:
        print ":heavy_check_mark:"
    elif success == False:
        print ":heavy_multiplication_x:"
    elif success is None:
        print ":heavy_minus_sign:"

    print "---"
    
    if mounted:
        print "Unmount | bash=$0 param1=--unmount"
    else:
        print "Mount | bash=$0 param1=--mount"
    
    if stopped:
        print "Restart | bash=$0 param1=--restart"
    else:
        print "Stop | bash=$0 param1=--stop"

if __name__ == '__main__':
    main()
