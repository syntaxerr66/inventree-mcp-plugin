#!/usr/bin/env bash

# Copyright (c) 2021-2026 community-scripts ORG
# Author: Slaviša Arežina (tremor021)
# License: MIT | https://github.com/community-scripts/ProxmoxVE/raw/main/LICENSE
# Source: https://github.com/inventree/InvenTree

source /dev/stdin <<<"$FUNCTIONS_FILE_PATH"
color
verb_ip6
catch_errors
setting_up_container
network_check
update_os

msg_info "Setting up InvenTree Repository"
setup_deb822_repo \
  "inventree" \
  "https://dl.packager.io/srv/inventree/InvenTree/key" \
  "https://dl.packager.io/srv/deb/inventree/InvenTree/stable/$(get_os_info id)" \
  "$(get_os_info version)" \
  "main"
msg_ok "Set up InvenTree Repository"

msg_info "Installing InvenTree (Patience)"
export SETUP_NO_CALLS=true
$STD apt install -y inventree
msg_ok "Installed InvenTree"

msg_info "Configuring InvenTree"
if [[ -f /etc/inventree/config.yaml ]]; then
  sed -i "s|site_url:.*|site_url: http://${LOCAL_IP}|" /etc/inventree/config.yaml
fi
$STD inventree run invoke update
msg_ok "Configured InvenTree"

msg_info "Installing MCP Plugin"
# Enable plugins in config.yaml
if [[ -f /etc/inventree/config.yaml ]]; then
  if grep -q "^plugins_enabled:" /etc/inventree/config.yaml; then
    sed -i "s|^plugins_enabled:.*|plugins_enabled: true|" /etc/inventree/config.yaml
  elif grep -q "^#.*plugins_enabled:" /etc/inventree/config.yaml; then
    sed -i "s|^#.*plugins_enabled:.*|plugins_enabled: true|" /etc/inventree/config.yaml
  else
    echo "plugins_enabled: true" >> /etc/inventree/config.yaml
  fi
fi

# Add MCP plugin to plugins.txt so it persists across InvenTree upgrades
PLUGINS_FILE="/etc/inventree/plugins.txt"
if [[ -f "$PLUGINS_FILE" ]]; then
  if ! grep -q "inventree-mcp-plugin" "$PLUGINS_FILE"; then
    echo "inventree-mcp-plugin @ https://github.com/syntaxerr66/inventree-mcp-plugin/archive/refs/heads/master.tar.gz" >> "$PLUGINS_FILE"
  fi
else
  echo "# InvenTree Plugins (uses PIP framework to install)" > "$PLUGINS_FILE"
  echo "inventree-mcp-plugin @ https://github.com/syntaxerr66/inventree-mcp-plugin/archive/refs/heads/master.tar.gz" >> "$PLUGINS_FILE"
fi

# Install the plugin into InvenTree's venv (tarball URL, no git required)
$STD /opt/inventree/env/bin/pip install "https://github.com/syntaxerr66/inventree-mcp-plugin/archive/refs/heads/master.tar.gz"
msg_ok "Installed MCP Plugin"

motd_ssh
customize
cleanup_lxc
