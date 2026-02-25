# Installation Guide

This guide covers installing the InvenTree MCP plugin across all supported deployment types.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Install (LXC / Bare-Metal)](#quick-install-lxc--bare-metal)
- [Installation by Deployment Type](#installation-by-deployment-type)
  - [Proxmox LXC Container (PKG Installer)](#proxmox-lxc-container-pkg-installer)
  - [Docker / Docker Compose](#docker--docker-compose)
  - [Bare-Metal / Source Install](#bare-metal--source-install)
- [Post-Install Configuration](#post-install-configuration)
  - [Enable Plugins](#1-enable-plugins)
  - [Activate the MCP Plugin](#2-activate-the-mcp-plugin)
  - [Enable URL Integration](#3-enable-url-integration)
  - [Get an API Token](#4-get-an-api-token)
- [Connecting MCP Clients](#connecting-mcp-clients)
  - [Claude Code (CLI)](#claude-code-cli)
  - [Claude Desktop](#claude-desktop)
  - [Other MCP Clients](#other-mcp-clients)
- [Optional: Image Search Setup](#optional-image-search-setup)
- [Upgrading](#upgrading)
- [Uninstalling](#uninstalling)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- InvenTree **v1.0.0 or later** (tested on v1.1.x)
- Python **3.9+** (ships with InvenTree)
- A superuser account on the InvenTree instance
- Network access between your MCP client and the InvenTree server

---

## Quick Install (LXC / Bare-Metal)

For Proxmox LXC containers and bare-metal installs, SSH into your InvenTree server and run:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/syntaxerr66/inventree-mcp-plugin/master/install-mcp-plugin.sh)
```

This auto-detects your InvenTree installation, installs the plugin, enables plugins in the config, adds it to `plugins.txt` for persistence, and restarts InvenTree.

After running the script, follow [Post-Install Configuration](#post-install-configuration) to activate the plugin in the web UI.

For Docker installs, see [Docker / Docker Compose](#docker--docker-compose) below.

---

## Installation by Deployment Type

### Proxmox LXC Container (PKG Installer)

This is the most common setup when InvenTree is deployed via the [community Proxmox helper scripts](https://github.com/community-scripts/ProxmoxVE). The PKG installer puts InvenTree at `/opt/inventree` with a Python venv at `/opt/inventree/env`.

#### Automated

SSH into the LXC container and run the install script:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/syntaxerr66/inventree-mcp-plugin/master/install-mcp-plugin.sh)
```

Then follow [Post-Install Configuration](#post-install-configuration).

#### Manual

1. **SSH into the LXC container:**

   ```bash
   ssh root@<container-ip>
   ```

2. **Install the plugin into InvenTree's venv:**

   ```bash
   /opt/inventree/env/bin/pip install https://github.com/syntaxerr66/inventree-mcp-plugin/archive/refs/heads/master.tar.gz
   ```

3. **Add it to plugins.txt so it persists across InvenTree upgrades:**

   ```bash
   echo "inventree-mcp-plugin @ https://github.com/syntaxerr66/inventree-mcp-plugin/archive/refs/heads/master.tar.gz" >> /etc/inventree/plugins.txt
   ```

4. **Enable plugins in config.yaml** (if not already):

   ```bash
   sed -i 's/^#.*plugins_enabled:.*/plugins_enabled: true/' /etc/inventree/config.yaml
   ```

   Or manually edit `/etc/inventree/config.yaml` and set:
   ```yaml
   plugins_enabled: true
   ```

5. **Restart InvenTree:**

   ```bash
   inventree restart
   ```

6. **Continue to [Post-Install Configuration](#post-install-configuration).**

---

### Docker / Docker Compose

InvenTree's Docker setup uses a data volume (typically `inventree-data`) mounted at `/home/inventree/data` inside the container. Plugins are installed via a `plugins.txt` file on this volume.

1. **Find your InvenTree data volume location.**

   If you used the official `docker-compose.yml`, the volume path is set by `INVENTREE_EXT_VOLUME` in your `.env` file. Common locations:

   ```bash
   # Check your .env file
   grep INVENTREE_EXT_VOLUME .env

   # Or find the mounted volume
   docker inspect inventree-server | grep -A5 Mounts
   ```

2. **Add the plugin to `plugins.txt`:**

   ```bash
   # Replace /path/to/inventree-data with your actual data volume path
   echo "inventree-mcp-plugin @ https://github.com/syntaxerr66/inventree-mcp-plugin/archive/refs/heads/master.tar.gz" >> /path/to/inventree-data/plugins.txt
   ```

   If `plugins.txt` doesn't exist yet, create it:

   ```bash
   echo "# InvenTree Plugins" > /path/to/inventree-data/plugins.txt
   echo "inventree-mcp-plugin @ https://github.com/syntaxerr66/inventree-mcp-plugin/archive/refs/heads/master.tar.gz" >> /path/to/inventree-data/plugins.txt
   ```

3. **Enable plugins in your `.env` file:**

   ```bash
   # Add or update in your .env file
   INVENTREE_PLUGINS_ENABLED=true
   ```

4. **Enable "Check Plugins on Startup"** so plugins are auto-installed when containers restart:

   This can be set in `.env`:
   ```bash
   INVENTREE_PLUGIN_ON_STARTUP=true
   ```

   Or enabled later in the InvenTree web UI under Settings > Plugin Settings.

5. **Restart the containers:**

   ```bash
   docker compose restart
   ```

   Or, if you want a clean restart:

   ```bash
   docker compose down && docker compose up -d
   ```

6. **Verify the plugin was installed:**

   ```bash
   docker exec inventree-server pip list | grep inventree-mcp
   ```

7. **Continue to [Post-Install Configuration](#post-install-configuration).**

---

### Bare-Metal / Source Install

For InvenTree installed from source (the "production server" setup), the typical layout is:
- Source code: `/home/inventree/src/`
- Virtual environment: `/home/inventree/env/`
- Config: `/home/inventree/src/InvenTree/config.yaml`

#### Automated

SSH into the server and run the install script:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/syntaxerr66/inventree-mcp-plugin/master/install-mcp-plugin.sh)
```

Then follow [Post-Install Configuration](#post-install-configuration).

#### Manual

1. **Activate InvenTree's virtualenv:**

   ```bash
   source /home/inventree/env/bin/activate
   ```

2. **Install the plugin:**

   ```bash
   pip install https://github.com/syntaxerr66/inventree-mcp-plugin/archive/refs/heads/master.tar.gz
   ```

3. **Add to plugins.txt** (so `invoke update` preserves it):

   ```bash
   # plugins.txt is in the same directory as config.yaml
   echo "inventree-mcp-plugin @ https://github.com/syntaxerr66/inventree-mcp-plugin/archive/refs/heads/master.tar.gz" >> /home/inventree/src/InvenTree/plugins.txt
   ```

4. **Enable plugins in `config.yaml`:**

   ```yaml
   plugins_enabled: true
   ```

5. **Restart services:**

   ```bash
   sudo supervisorctl restart all
   ```

   Or if using systemd:

   ```bash
   sudo systemctl restart inventree-web inventree-worker
   ```

6. **Continue to [Post-Install Configuration](#post-install-configuration).**

---

## Post-Install Configuration

After installing the package, you need to activate the plugin and enable URL integration through the InvenTree web UI or API. These steps apply to **all deployment types**.

### 1. Enable Plugins

If you haven't already enabled plugins via config file or environment variable, do so now:

- **Web UI:** Go to **Settings** (gear icon) > **Plugin Settings** > enable **"Plugins enabled"**
- **Config:** Set `plugins_enabled: true` in `config.yaml`
- **Env var:** Set `INVENTREE_PLUGINS_ENABLED=true`

A server restart is required after enabling plugins for the first time.

### 2. Activate the MCP Plugin

Newly installed plugins are **disabled by default**.

1. Go to **Settings** > **Plugin Settings** > **Plugins**
2. Find **"InvenTree MCP Server"** in the list
3. Toggle the switch to **activate** it

Alternatively, via the API:

```bash
curl -X PATCH http://<inventree-host>/api/plugins/inventree-mcp/ \
  -H "Authorization: Token <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"active": true}'
```

### 3. Enable URL Integration

The MCP plugin registers a URL endpoint (`/plugin/inventree-mcp/mcp`). InvenTree requires URL integration to be explicitly enabled.

1. Go to **Settings** > **Plugin Settings**
2. Enable **"Enable URL integration"**
3. InvenTree will prompt for a **server restart** — restart when prompted

Alternatively, via the API:

```bash
curl -X PATCH http://<inventree-host>/api/settings/global/ENABLE_PLUGINS_URL/ \
  -H "Authorization: Token <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"value": true}'
```

Then restart InvenTree (method depends on your deployment type — see above).

### 4. Get an API Token

MCP clients authenticate using an InvenTree API token. To get one:

**Via the Web UI:**
1. Click your profile icon > **Account Settings**
2. Under **API Tokens**, click **Create** to generate a new token
3. Copy the token (it starts with `inv-...`)

**Via the API with basic auth:**

```bash
curl -u "admin:your-password" http://<inventree-host>/api/user/token/
```

Response:
```json
{"token": "inv-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxx"}
```

### Verify Everything Works

Test the MCP endpoint with curl:

```bash
# Initialize a session
curl -X POST http://<inventree-host>/plugin/inventree-mcp/mcp \
  -H "Authorization: Token inv-..." \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "1.0"}
    }
  }'
```

If you get a JSON response with `serverInfo`, the plugin is working.

---

## Connecting MCP Clients

The MCP endpoint URL is:

```
http://<inventree-host>/plugin/inventree-mcp/mcp
```

### Claude Code (CLI)

Add the server to your Claude Code MCP configuration. Edit `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "inventree": {
      "httpUrl": "http://<inventree-host>/plugin/inventree-mcp/mcp",
      "headers": {
        "Authorization": "Token inv-your-token-here"
      }
    }
  }
}
```

Then restart Claude Code. You should see the InvenTree tools listed when Claude starts.

### Claude Desktop

Edit your Claude Desktop configuration file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "inventree": {
      "type": "streamableHttp",
      "url": "http://<inventree-host>/plugin/inventree-mcp/mcp",
      "headers": {
        "Authorization": "Token inv-your-token-here"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

### Other MCP Clients

Any MCP client that supports **Streamable HTTP transport** can connect. The key details:

| Setting | Value |
|---------|-------|
| Transport | Streamable HTTP |
| URL | `http://<host>/plugin/inventree-mcp/mcp` |
| Auth Header | `Authorization: Token inv-...` |
| Content-Type | `application/json` |
| Accept | `application/json, text/event-stream` |

The server implements the full MCP protocol including session management via the `Mcp-Session-Id` header.

---

## Optional: Image Search Setup

The `search_part_images` tool uses Google Custom Search to find images for parts. This is optional — all other tools work without it.

1. Create a [Google Cloud project](https://console.cloud.google.com/) and enable the **Custom Search JSON API**
2. Create an API key in the Google Cloud Console
3. Create a [Custom Search Engine](https://programmablesearchengine.google.com/) configured for image search
4. In InvenTree, go to **Settings** > **Plugin Settings** > **InvenTree MCP Server**
5. Enter your **Google API Key** and **Google CSE ID**

---

## Upgrading

### LXC / Bare-Metal

Re-run the install script — it handles everything:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/syntaxerr66/inventree-mcp-plugin/master/install-mcp-plugin.sh)
```

Or manually:

```bash
/opt/inventree/env/bin/pip install --upgrade https://github.com/syntaxerr66/inventree-mcp-plugin/archive/refs/heads/master.tar.gz
inventree restart
```

### Docker

The plugin is reinstalled from `plugins.txt` on each container start (if "Check Plugins on Startup" is enabled). To force an upgrade:

```bash
docker compose restart
```

---

## Uninstalling

### 1. Deactivate the plugin

In the InvenTree web UI: **Settings** > **Plugin Settings** > toggle off **InvenTree MCP Server**.

### 2. Remove the package

**LXC / Bare-Metal:**
```bash
/opt/inventree/env/bin/pip uninstall inventree-mcp-plugin
```

**Docker:** Remove the line from `plugins.txt` and restart:
```bash
docker compose restart
```

### 3. Clean up plugins.txt

Remove the `inventree-mcp-plugin` line from your `plugins.txt` file.

---

## Troubleshooting

### Plugin doesn't appear in the plugin list

- Verify plugins are enabled: check `plugins_enabled: true` in `config.yaml` or `INVENTREE_PLUGINS_ENABLED=true` in your environment
- Verify the package is installed: `pip list | grep inventree-mcp`
- Check InvenTree logs for import errors: `journalctl -u inventree-web-1 -n 50` (PKG installer) or `docker logs inventree-server --tail 50` (Docker)

### 404 when accessing the MCP endpoint

- **Enable URL integration:** Settings > Plugin Settings > "Enable URL integration" must be on
- A server restart is required after enabling URL integration
- Verify the plugin is **active** (not just installed)

### 403 Forbidden / CSRF errors

The plugin applies CSRF exemption automatically. If you still get 403s:
- Ensure you're sending the `Authorization` header (not using cookie-only auth for API calls)
- Check that the token is valid: `curl -H "Authorization: Token inv-..." http://<host>/api/`

### 302 Redirect instead of 401

InvenTree's middleware redirects unauthenticated requests to the login page. This means your token is missing or invalid. Double-check the `Authorization` header format — it must be `Token inv-...` (not `Bearer`).

### "Authentication credentials were not provided"

- The token format must be exactly: `Authorization: Token inv-xxxx`
- Verify the token is valid and belongs to an active user
- Check that InvenTree's `ApiTokenAuthentication` is working: test with `curl -H "Authorization: Token inv-..." http://<host>/api/`

### Tools list works but tool calls fail with async errors

If you see `SynchronousOnlyOperation` or "You cannot call this from an async context", you're running an older version of the plugin. Upgrade to the latest:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/syntaxerr66/inventree-mcp-plugin/master/install-mcp-plugin.sh)
```

### Database locked errors (SQLite)

InvenTree's default SQLite backend uses file-level locking. If you're making many concurrent MCP calls (e.g., bulk imports), you may see 500 errors. Solutions:
- Limit concurrent operations to 3-5 at a time
- Consider switching to PostgreSQL for production use
- Retry failed operations — they typically succeed once the lock clears
