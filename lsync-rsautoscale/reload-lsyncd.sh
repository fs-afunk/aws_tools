#!/bin/bash

LAST_HASH=$(< ~/.lsyncd_config_hash)
CURRENT_HASH=$(md5sum /etc/lsyncd.conf | awk '{print $1}')

echo "Current Hash $CURRENT_HASH"
echo "Last Hash $LAST_HASH"

if [[ "$LAST_HASH" != "$CURRENT_HASH" ]]; then
  echo 'lsync config hash changed'
  /sbin/service lsyncd restart
  echo $CURRENT_HASH > ~/.lsyncd_config_hash
else
  echo 'lsync config not updated'
fi
