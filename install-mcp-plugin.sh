#!/usr/bin/env bash
set -euo pipefail

# Install the InvenTree MCP Plugin into an existing InvenTree instance.
# Run this inside your InvenTree server (LXC container, VM, bare-metal).
#
# Usage:
#   bash <(curl -fsSL https://raw.githubusercontent.com/syntaxerr66/inventree-mcp-plugin/master/install-mcp-plugin.sh)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[+]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[x]${NC} $1"; exit 1; }

PLUGIN_URL="https://github.com/syntaxerr66/inventree-mcp-plugin/archive/refs/heads/master.tar.gz"
PLUGIN_LINE="inventree-mcp-plugin @ ${PLUGIN_URL}"

# --- Detect InvenTree installation ---

if [[ -d /opt/inventree/env ]]; then
  # PKG / Proxmox LXC install
  PIP="/opt/inventree/env/bin/pip"
  CONFIG="/etc/inventree/config.yaml"
  PLUGINS_FILE="/etc/inventree/plugins.txt"
  RESTART_CMD="inventree restart"
  info "Detected PKG installer (venv at /opt/inventree/env)"

elif [[ -d /home/inventree/env ]]; then
  # Bare-metal / source install
  PIP="/home/inventree/env/bin/pip"
  CONFIG="/home/inventree/src/InvenTree/config.yaml"
  PLUGINS_FILE="/home/inventree/src/InvenTree/plugins.txt"
  RESTART_CMD="sudo supervisorctl restart all"
  info "Detected source install (venv at /home/inventree/env)"

else
  error "Could not find InvenTree installation. Expected venv at /opt/inventree/env or /home/inventree/env"
fi

# --- Install the plugin ---

info "Installing inventree-mcp-plugin..."
$PIP install "$PLUGIN_URL" 2>&1 | tail -3
info "Plugin installed"

# --- Add to plugins.txt for persistence ---

if [[ -f "$PLUGINS_FILE" ]]; then
  if ! grep -q "inventree-mcp-plugin" "$PLUGINS_FILE"; then
    echo "$PLUGIN_LINE" >> "$PLUGINS_FILE"
    info "Added to $PLUGINS_FILE"
  else
    info "Already in $PLUGINS_FILE"
  fi
else
  echo "# InvenTree Plugins (uses PIP framework to install)" > "$PLUGINS_FILE"
  echo "$PLUGIN_LINE" >> "$PLUGINS_FILE"
  info "Created $PLUGINS_FILE"
fi

# --- Enable plugins in config.yaml ---

if [[ -f "$CONFIG" ]]; then
  if grep -q "^plugins_enabled: true" "$CONFIG"; then
    info "Plugins already enabled in config"
  elif grep -q "^plugins_enabled:" "$CONFIG"; then
    sed -i "s|^plugins_enabled:.*|plugins_enabled: true|" "$CONFIG"
    info "Enabled plugins in $CONFIG"
  elif grep -q "^#.*plugins_enabled:" "$CONFIG"; then
    sed -i "s|^#.*plugins_enabled:.*|plugins_enabled: true|" "$CONFIG"
    info "Enabled plugins in $CONFIG"
  else
    echo "plugins_enabled: true" >> "$CONFIG"
    info "Added plugins_enabled to $CONFIG"
  fi
else
  warn "Config file not found at $CONFIG — enable plugins_enabled manually"
fi

# --- Restart InvenTree ---

info "Restarting InvenTree..."
if $RESTART_CMD 2>&1 | tail -2; then
  info "InvenTree restarted"
else
  warn "Restart command failed — try running: $RESTART_CMD"
fi

echo ""
info "Installation complete!"
echo ""
echo -e "  ${YELLOW}Next steps:${NC}"
echo "  1. Log into the InvenTree web UI as an admin"
echo "  2. Go to Settings > Plugin Settings"
echo "  3. Activate 'InvenTree MCP Server'"
echo "  4. Enable 'Enable URL integration'"
echo "  5. Restart InvenTree when prompted"
echo ""
echo -e "  The MCP endpoint will be available at:"
echo -e "  ${GREEN}http://<your-host>/plugin/inventree-mcp/mcp${NC}"
echo ""
echo -e "  See ${YELLOW}INSTALL.md${NC} for MCP client setup (Claude Code, Claude Desktop):"
echo -e "  https://github.com/syntaxerr66/inventree-mcp-plugin/blob/master/INSTALL.md"
