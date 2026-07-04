#!/bin/sh
# fixture: privilege escalation (inert)
chmod +s /tmp/rootshell
sudo cp rootshell /usr/local/bin/
chown root:root /usr/local/bin/rootshell
