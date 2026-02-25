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
# Enable plugins in config.yaml if not already enabled
if [[ -f /etc/inventree/config.yaml ]]; then
  if grep -q "^plugins_enabled:" /etc/inventree/config.yaml; then
    sed -i "s|^plugins_enabled:.*|plugins_enabled: true|" /etc/inventree/config.yaml
  elif grep -q "^#.*plugins_enabled:" /etc/inventree/config.yaml; then
    sed -i "s|^#.*plugins_enabled:.*|plugins_enabled: true|" /etc/inventree/config.yaml
  else
    echo "plugins_enabled: true" >> /etc/inventree/config.yaml
  fi
fi

# Add MCP plugin to plugins.txt
PLUGINS_FILE="/etc/inventree/plugins.txt"
if [[ -f "$PLUGINS_FILE" ]]; then
  if ! grep -q "inventree-mcp-plugin" "$PLUGINS_FILE"; then
    echo "inventree-mcp-plugin @ git+https://github.com/syntaxerr66/inventree-mcp-plugin.git" >> "$PLUGINS_FILE"
  fi
else
  echo "# InvenTree Plugins (uses PIP framework to install)" > "$PLUGINS_FILE"
  echo "inventree-mcp-plugin @ git+https://github.com/syntaxerr66/inventree-mcp-plugin.git" >> "$PLUGINS_FILE"
fi

# Install the plugin and its dependencies into InvenTree's venv
$STD /opt/inventree/env/bin/pip install "git+https://github.com/syntaxerr66/inventree-mcp-plugin.git"

# Restart InvenTree to pick up the new plugin
$STD inventree restart
msg_ok "Installed MCP Plugin"

msg_info "Enabling MCP Plugin"
# Wait for InvenTree to fully start
sleep 5

# Create a temporary superuser token and enable plugin settings via the API.
# The PKG installer creates a default admin user; use manage.py to generate a token.
INVENTREE_TOKEN=$(/opt/inventree/env/bin/python /opt/inventree/src/backend/InvenTree/manage.py shell -c "
from users.models import ApiToken
from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.filter(is_superuser=True).first()
if admin:
    token, _ = ApiToken.objects.get_or_create(user=admin)
    print(token.key)
" 2>/dev/null)

if [[ -n "$INVENTREE_TOKEN" ]]; then
  # Enable URL integration (required for MCP endpoint)
  curl -s -X PATCH "http://localhost/api/settings/global/ENABLE_PLUGINS_URL/" \
    -H "Authorization: Token $INVENTREE_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"value": true}' > /dev/null 2>&1

  # Activate the MCP plugin
  curl -s -X PATCH "http://localhost/api/plugins/inventree-mcp/" \
    -H "Authorization: Token $INVENTREE_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"active": true}' > /dev/null 2>&1

  # Restart again after enabling URL integration (required by InvenTree)
  $STD inventree restart
  sleep 3
  msg_ok "Enabled MCP Plugin"
else
  msg_warn "Could not auto-enable MCP plugin — enable it manually in InvenTree Settings > Plugins"
fi

motd_ssh
customize
cleanup_lxc
