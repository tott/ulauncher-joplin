# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Ulauncher extension for quickly creating notes and todos in Joplin. It integrates with Joplin's REST API (Web Clipper service) to allow users to create notes and todos directly from Ulauncher.

## Architecture

### Core Components

**JoplinExtension (main.py:14-36)**
- Main extension class that inherits from `ulauncher.api.client.Extension`
- Manages event subscriptions and handles communication with Joplin's REST API
- Key methods:
  - `add_note()`: POSTs to `http://localhost:41184/notes` to create notes/todos
  - `get_notebooks()`: GETs from `http://localhost:41184/folders` to fetch notebook list

### Event Flow

1. **KeywordQueryEventListener** (main.py:102-173): Handles user input with two modes:

   **Config Mode** (triggered by "config" query, main.py:111-112):
   - Calls `_show_config_notebooks()` method (main.py:149-173)
   - Shows ALL notebooks sorted by note count
   - Current default is marked with ★ star prefix
   - Each result carries config action data: `{action: 'set_default', type, notebookId}`

   **Normal Mode** (any other query):
   - If a default notebook is configured for the keyword type, fetches and displays it first with "DEFAULT:" prefix (main.py:121-133)
   - Fetches all notebooks from Joplin API
   - Sorts notebooks by note count (descending) to prioritize most-used notebooks
   - Returns list of notebooks limited by user preference setting
   - Each result carries custom action data: `{text, type, notebookId}`

2. **ItemEnterEventListener** (main.py:60-83): Handles notebook selection with two actions:

   **Set Default Action** (data.action == 'set_default', main.py:65-80):
   - Saves notebook ID to extension preferences
   - Updates in-memory preference value
   - Persists preferences to disk using `extension.preferences.save()`
   - Returns `HideWindowAction()` to close Ulauncher

   **Create Note Action** (all other data):
   - Calls `add_note()` to create the note/todo in selected notebook

3. **PreferencesEventListener** and **PreferencesUpdateEventListener** (main.py:86-115)
   - Manage extension settings including limit, server, token, and default notebooks
   - Default fallback for limit: 10 notebooks

### Joplin API Integration

The extension uses Joplin's REST API with configurable server address and authentication:
- **POST /notes?token={token}**: Creates notes with `{title, is_todo, parent_id}` (main.py:35-41)
- **GET /folders?token={token}**: Retrieves notebook list with note counts (main.py:43-47)
- **GET /folders/{id}?token={token}**: Retrieves a specific notebook by ID (main.py:49-59)

**Authentication**: All API requests include the token as a query parameter for authentication.

**Request Handling**:
- All API requests have a 5-second timeout to prevent hanging
- HTTP errors are caught and raise exceptions with `raise_for_status()`
- Error handling displays user-friendly messages for common issues

**Important**: Joplin Web Clipper service must be running for this extension to work. The API token can be found in Joplin under Tools → Options → Web Clipper.

## Configuration

**manifest.json**: Defines extension metadata and user preferences
- `kw_note`: Keyword for creating notes (default: "note")
- `kw_todo`: Keyword for creating todos (default: "todo")
- `server`: Joplin server address (default: "http://localhost:41184")
- `token`: Joplin API token (required for authentication, no default)
- `default_note_notebook`: Default notebook ID for notes (optional, no default)
- `default_todo_notebook`: Default notebook ID for todos (optional, no default)
- `limit`: Number of notebooks to display (default: "5")

**Configuration Flow**:
- Settings are loaded via `PreferencesEventListener` on extension startup (main.py:86-97)
- Updates are handled via `PreferencesUpdateEventListener` (main.py:100-115)
- Settings can also be updated programmatically via config commands (main.py:70-78)
- All settings are stored in `JoplinExtension` instance variables (main.py:19-26)

**Default Notebooks Feature**:
- When a default notebook ID is configured, it appears first in the results list
- Default notebooks are fetched using `get_notebook_by_id()` to display their titles
- Displayed with "DEFAULT:" prefix to distinguish from other notebooks
- Separate defaults can be configured for notes and todos
- Users can set defaults interactively by typing `note config` or `todo config` commands
- Config mode shows all notebooks with current default marked by ★ star

## Dependencies

Required Python libraries (must be installed in Ulauncher's Python environment):
- `requests`: For HTTP communication with Joplin API
- `json`: For JSON serialization (standard library)

## Testing the Extension

To test changes:
1. Ensure Joplin is running with Web Clipper service enabled (Tools → Options → Web Clipper in Joplin)
2. Restart Ulauncher or reload the extension
3. Type `note test note` or `todo test todo` in Ulauncher
4. Verify notebook list appears sorted by note count
5. Select a notebook to create the note/todo
