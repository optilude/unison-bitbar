# Unison Sync Bitbar plugin

This is a plugin for Bitbar (https://getbitbar.com) to manage a Unison
(https://www.cis.upenn.edu/~bcpierce/unison/) file synchronisation process.

First of all, you must install Unison, and the `unison` binary must be on the
path (e.g. in `/usr/bin` or `/usr/local/bin`).

You must then create a default Unison profile in `~/.unison/default.conf` that
sets all options you need for synchronisation. See the Unison manual, as well
as the `example.conf` file in this repository.

In this file, you should add two special lines, which will be ignored by Unison,
but parsed by the plugin:

    # sync:mounturi = smb://username@server/fileshare
    # sync:mountpoint = /Volumes/fileshare

These specify a URL to attempt to mount using the OSX `open` command (which will
cause the Finder to attempt to mount with default options) and the path where
the shared drive will be mounted (usually `/Volumes/<name of fileshare>`).

These are used to attempt to automatically mount the shared drive and to check
for its existence before running Unison.

The plugin will run automatically on the specified frequency (e.g. save in the
Bitbar plugin directory as `unison-sync.15m.py` to run every 15 minutes) unless
stopped. The `Stop` command in the menu will create a file
`~/.unison/unison-sync.stopped`. When this file is present, no syncing will be
attempted. The `Restart` command simply deletes the file.

## Troubleshooting

It is a good idea to test your Unison configuration first without the plugin.
Simply run `unison default.conf` to execute the command that the plugin will
run.

To test the plugin itself, run it on the command line (it should be executable,
if not do `chmod +x unison-sync.py` first). It accepts various flags, which
can be seen with the `--help` option.
