# inventree-mcp-plugin

A native InvenTree plugin that exposes inventory operations as MCP tools over Streamable HTTP transport.

Unlike a standalone MCP server that communicates with InvenTree via REST API, this plugin runs **inside** InvenTree as a Django plugin. It has direct ORM access — no HTTP round-trips, no serialization overhead, and DRF authentication comes for free.

## Features

- **26 MCP tools** covering parts, stock, locations, and categories
- **Direct ORM access** — queries go straight to the database
- **Streamable HTTP transport** — network-accessible MCP endpoint
- **DRF authentication** — Token and Session auth supported
- **Icon validation** — validates Tabler icons against InvenTree's bundled icon set
- **Optional image search** — Google Custom Search integration for part images

## Quick Start

SSH into your InvenTree server and run:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/syntaxerr66/inventree-mcp-plugin/master/install-mcp-plugin.sh)
```

Then activate the plugin in Settings > Plugin Settings, enable "URL integration", and restart.

The MCP endpoint will be available at:

```
http://<inventree-host>/plugin/inventree-mcp/mcp
```

**See [INSTALL.md](INSTALL.md) for detailed instructions** covering Proxmox LXC, Docker, bare-metal installs, MCP client configuration, and troubleshooting.

## Usage

All requests require an InvenTree API token: `Authorization: Token inv-...`

```bash
# Search for parts
curl -X POST http://your-inventree/plugin/inventree-mcp/mcp \
  -H "Authorization: Token inv-..." \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_parts","arguments":{"search":"ESP32"}}}'
```

## Tools

### Parts (8 tools)
| Tool | Description |
|------|-------------|
| `search_parts` | Search parts by keyword |
| `get_part` | Get part details by ID |
| `create_part` | Create a new part |
| `update_part` | Update part fields |
| `delete_part` | Deactivate and delete a part |
| `list_parts` | List parts by category |
| `set_part_image` | Set part image from URL |
| `search_part_images` | Search Google for part images |

### Stock (7 tools)
| Tool | Description |
|------|-------------|
| `get_stock` | List stock items with filters |
| `get_stock_item` | Get stock item by ID |
| `add_stock` | Create new stock entry |
| `stock_add_quantity` | Add quantity to existing items |
| `stock_remove_quantity` | Remove quantity from items |
| `stock_transfer` | Transfer items between locations |
| `delete_stock_item` | Delete a stock item |

### Locations (6 tools)
| Tool | Description |
|------|-------------|
| `search_stock_locations` | Search locations by name |
| `get_stock_location` | Get location by ID |
| `list_stock_locations` | List locations with hierarchy |
| `create_stock_location` | Create a new location (supports icon) |
| `update_stock_location` | Update location fields (supports icon) |
| `delete_stock_location` | Delete an empty location |

### Categories (5 tools)
| Tool | Description |
|------|-------------|
| `search_part_categories` | Search categories by name |
| `list_part_categories` | List categories with hierarchy |
| `create_part_category` | Create a new category (supports icon) |
| `update_part_category` | Update category fields (supports icon) |
| `delete_part_category` | Delete an empty category |

## Icons

Category and location tools support setting Tabler icons via the `icon` parameter using the format `ti:<name>:<variant>` (e.g. `ti:tool:outline`, `ti:circle:filled`). Icons are validated against InvenTree's bundled `icons.json` — invalid names or variants are rejected with a helpful error message. Pass `icon: "none"` to clear an existing icon.

## Development

```bash
git clone https://github.com/syntaxerr66/inventree-mcp-plugin.git
cd inventree-mcp-plugin
pip install -e .
```

## License

MIT
