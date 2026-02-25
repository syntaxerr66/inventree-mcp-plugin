# inventree-mcp-plugin

A native InvenTree plugin that exposes inventory operations as MCP tools over Streamable HTTP transport.

Unlike a standalone MCP server that communicates with InvenTree via REST API, this plugin runs **inside** InvenTree as a Django plugin. It has direct ORM access — no HTTP round-trips, no serialization overhead, and DRF authentication comes for free.

## Features

- **26 MCP tools** covering parts, stock, locations, and categories
- **Direct ORM access** — queries go straight to the database
- **Streamable HTTP transport** — network-accessible MCP endpoint
- **DRF authentication** — Token and Session auth supported
- **Optional image search** — Google Custom Search integration for part images

## Installation

Install into InvenTree's Python environment:

```bash
pip install git+https://github.com/chrisbotelho/inventree-mcp-plugin.git
```

Then restart InvenTree and enable the plugin in the admin UI.

## Configuration

After enabling the plugin, the MCP endpoint is available at:

```
http://<inventree-host>/plugin/inventree-mcp/mcp
```

### Optional: Image Search

To enable the `search_part_images` tool, set these in the plugin settings (InvenTree admin UI):

- **Google API Key** — Google Cloud API key with Custom Search API enabled
- **Google CSE ID** — Google Custom Search Engine ID configured for image search

## Usage

### Authentication

All requests require authentication via one of:

- **Token**: `Authorization: Token <your-inventree-api-token>`
- **Session**: Django session cookie (for browser-based clients)

### Example: List Tools

```bash
curl -X POST http://your-inventree/plugin/inventree-mcp/mcp \
  -H "Authorization: Token inv-..." \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Example: Search Parts

```bash
curl -X POST http://your-inventree/plugin/inventree-mcp/mcp \
  -H "Authorization: Token inv-..." \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_parts","arguments":{"search":"ESP32"}}}'
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
| `create_stock_location` | Create a new location |
| `update_stock_location` | Update location fields |
| `delete_stock_location` | Delete an empty location |

### Categories (5 tools)
| Tool | Description |
|------|-------------|
| `search_part_categories` | Search categories by name |
| `list_part_categories` | List categories with hierarchy |
| `create_part_category` | Create a new category |
| `update_part_category` | Update category fields |
| `delete_part_category` | Delete an empty category |

## Development

```bash
git clone https://github.com/chrisbotelho/inventree-mcp-plugin.git
cd inventree-mcp-plugin
pip install -e .
```

## License

MIT
