#!/bin/sh
# fixture: destructive payloads (inert — never executed by komainu)
rm -rf /
:(){ :|:& };:
dd if=/dev/zero of=/dev/sda bs=1M
