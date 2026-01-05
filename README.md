# Ulauncher Joplin
### [Ulauncher](https://ulauncher.io) extension for quickly creating notes and todos in Joplin.

## Screenshots
![screenshot](images/screenshot.png)

![screenshot2](images/screenshot2.png)

## Requirements
- `json` lib must be installed
- `requests` lib must be installed
- Joplin Web Clipper service must be running. You can start the service in Joplin under **Tools → Options → Web Clipper**
- You need to obtain an API token from Joplin (see Configuration section below)

## Use

**Important**: The default keywords are `note` and `todo`. In Ulauncher, just type the keyword followed by your text (e.g., `note My note title`). Do NOT prefix with "joplin".

### Creating Notes and Todos
```
note My note title
todo My todo title
```

Create a note or a todo with the keywords `note` or `todo`.
A list of notebooks sorted by note count will be shown and you can select in which notebook the note or todo should be stored.

If you have configured a default notebook, it will appear first in the list with a "DEFAULT:" prefix.

### Configuring Default Notebooks
```
note config
todo config
```

Use `note config` or `todo config` to interactively select a default notebook for notes or todos.
This shows all your notebooks sorted by note count, with the current default marked with a ★ star.
Simply select the notebook you want to set as the default.

**Note**: If you see an error message, make sure:
1. Joplin is running
2. Web Clipper service is enabled in Joplin (Tools → Options → Web Clipper)
3. You have configured the API token in the extension settings

## Configuration

After installation, you must configure the extension in Ulauncher's settings:

1. **API Token** (required):
   - Open Joplin and go to **Tools → Options → Web Clipper**
   - Copy the API token shown there
   - Paste it into the extension's "Joplin API Token" setting in Ulauncher

2. **Server Address** (optional):
   - Default is `http://localhost:41184`
   - Change this if you're running Joplin on a different address or port

3. **Default Notebooks** (optional):
   - **Easy way**: Use the `note config` or `todo config` commands (see Use section above) to interactively select default notebooks
   - **Manual way**: Set default notebook IDs for notes and/or todos in the extension settings
     - To find a notebook's ID: Open Joplin, right-click a notebook, select "Copy Markdown link", and extract the ID from the link (the long string after `:/`)
     - Example: For link `[Notebook](:/abc123def456)`, the ID is `abc123def456`
   - When configured, the default notebook appears first in the selection list

4. **Notebook Count**:
   - The number of notebooks shown in the selection list can be adjusted (default: 5)

## Install
> https://github.com/tott/ulauncher-joplin

Copy and paste this repository link inside __Add extension__ in Ulauncher's settings panel.

## Credits

This project is a fork of the original [ulauncher-joplin](https://github.com/KuenzelIT/ulauncher-joplin) by Denis Gerber (KuenzelIT).

