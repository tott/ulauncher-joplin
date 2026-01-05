import json
import requests

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent, SystemExitEvent, PreferencesUpdateEvent, \
    PreferencesEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction


# Using the REST-Api of Joplin: https://joplinapp.org/api/references/rest_api/
class JoplinExtension(Extension):
    def __init__(self):
        super(JoplinExtension, self).__init__()

        # Number of notebooks that should be suggested
        self.limit = None
        # Joplin server address
        self.server = None
        # Joplin API token
        self.token = None
        # Default notebook IDs
        self.default_note_notebook = None
        self.default_todo_notebook = None

        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(SystemExitEvent, SystemExitEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

    def add_note(self, note):
        url = f"{self.server}/notes?token={self.token}"
        requests.post(url, json.dumps({
            'title': note['text'],
            'is_todo': note['type'] == 'todo',
            'parent_id': note['notebookId']
        }), timeout=5)

    def get_notebooks(self):
        url = f"{self.server}/folders?token={self.token}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        # Check if response has 'items' key (paginated response)
        if isinstance(data, dict) and 'items' in data:
            return data['items']
        # Otherwise assume it's already a list
        return data

    def get_notebook_by_id(self, notebook_id):
        """Get a specific notebook by ID"""
        if not notebook_id:
            return None
        url = f"{self.server}/folders/{notebook_id}?token={self.token}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except:
            return None


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        data = event.get_data()

        # Check if this is a config action
        if data.get('action') == 'set_default':
            note_type = data['type']
            notebook_id = data['notebookId']

            # Save the preference
            if note_type == 'note':
                extension.preferences['default_note_notebook'] = notebook_id
                extension.default_note_notebook = notebook_id
            else:
                extension.preferences['default_todo_notebook'] = notebook_id
                extension.default_todo_notebook = notebook_id

            # Save preferences to disk
            extension.preferences.save()

            return HideWindowAction()
        else:
            # Regular note/todo creation
            extension.add_note(data)


class PreferencesEventListener(EventListener):
    def on_event(self, event, extension):
        try:
            n = int(event.preferences['limit'])
        except:
            n = 10
        extension.limit = n

        extension.server = event.preferences.get('server', 'http://localhost:41184')
        extension.token = event.preferences.get('token', '')
        extension.default_note_notebook = event.preferences.get('default_note_notebook', '')
        extension.default_todo_notebook = event.preferences.get('default_todo_notebook', '')


class PreferencesUpdateEventListener(EventListener):
    def on_event(self, event, extension):
        if event.id == 'limit':
            try:
                n = int(event.new_value)
                extension.limit = n
            except:
                pass
        elif event.id == 'server':
            extension.server = event.new_value
        elif event.id == 'token':
            extension.token = event.new_value
        elif event.id == 'default_note_notebook':
            extension.default_note_notebook = event.new_value
        elif event.id == 'default_todo_notebook':
            extension.default_todo_notebook = event.new_value


class SystemExitEventListener(EventListener):
    def on_event(self, event, extension):
        extension.close()


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        keyword = event.get_keyword()
        query = event.get_argument()

        if query == None:
            return None

        # Check if this is a config command
        if query.strip().lower() == 'config':
            return self._show_config_notebooks(keyword, extension)

        # Check if server and token are configured
        if not extension.server or not extension.token:
            results = []
            results.append(ExtensionResultItem(
                icon='images/icon.png',
                name="⚠ Configuration Required",
                description="Please configure Joplin server address and API token in extension settings",
                on_enter=HideWindowAction()
            ))
            return RenderResultListAction(results)

        try:
            notebooks = extension.get_notebooks()

            # Check if we got valid data
            if not notebooks or not isinstance(notebooks, list):
                results = []
                results.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name="⚠ No Notebooks Found",
                    description="Response type: %s, Length: %s. Is Joplin running with Web Clipper enabled?" % (type(notebooks).__name__, len(notebooks) if notebooks else 0),
                    on_enter=HideWindowAction()
                ))
                return RenderResultListAction(results)

            if len(notebooks) == 0:
                results = []
                results.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name="⚠ No Notebooks in Joplin",
                    description="Joplin has no notebooks. Create at least one notebook in Joplin first.",
                    on_enter=HideWindowAction()
                ))
                return RenderResultListAction(results)

            # Sort by note count. The notebook with the most notes should be on top.
            notebooks.sort(key=lambda x: x.get('note_count', 0), reverse=True)

            results = []

            # Add default notebook as first option if configured
            default_notebook_id = extension.default_note_notebook if keyword == 'note' else extension.default_todo_notebook
            if default_notebook_id:
                default_notebook = extension.get_notebook_by_id(default_notebook_id)
                if default_notebook:
                    data = {
                        'text': query,
                        'type': keyword,
                        'notebookId': default_notebook['id']
                    }
                    results.append(ExtensionResultItem(icon='images/icon.png',
                                                       name="Add %s to DEFAULT: %s" % (keyword, default_notebook['title']),
                                                       on_enter=ExtensionCustomAction(data, keep_app_open=False)))

            for notebook in notebooks[:extension.limit]:
                data = {
                    'text': query,
                    'type': keyword,
                    'notebookId': notebook['id']
                }
                results.append(ExtensionResultItem(icon='images/icon.png',
                                                   name="Add %s to notebook %s" % (keyword, notebook['title']),
                                                   on_enter=ExtensionCustomAction(data, keep_app_open=False)))

            return RenderResultListAction(results)

        except Exception as e:
            results = []
            results.append(ExtensionResultItem(
                icon='images/icon.png',
                name="⚠ Error Connecting to Joplin",
                description="Error: %s. Check server address and API token." % str(e),
                on_enter=HideWindowAction()
            ))
            return RenderResultListAction(results)

    def _show_config_notebooks(self, keyword, extension):
        """Show all notebooks for selecting a default"""
        results = []

        # Check if server and token are configured
        if not extension.server or not extension.token:
            results.append(ExtensionResultItem(
                icon='images/icon.png',
                name="⚠ Configuration Required",
                description="Please configure Joplin server address and API token in extension settings",
                on_enter=HideWindowAction()
            ))
            return RenderResultListAction(results)

        try:
            notebooks = extension.get_notebooks()

            # Check if we got valid data
            if not notebooks or not isinstance(notebooks, list):
                results.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name="⚠ No Notebooks Found",
                    description="Response type: %s, Length: %s. Is Joplin running?" % (type(notebooks).__name__, len(notebooks) if notebooks else 0),
                    on_enter=HideWindowAction()
                ))
                return RenderResultListAction(results)

            if len(notebooks) == 0:
                results.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name="⚠ No Notebooks in Joplin",
                    description="Joplin has no notebooks. Create at least one notebook in Joplin first.",
                    on_enter=HideWindowAction()
                ))
                return RenderResultListAction(results)

            notebooks.sort(key=lambda x: x.get('note_count', 0), reverse=True)

            # Get current default to highlight it
            current_default_id = extension.default_note_notebook if keyword == 'note' else extension.default_todo_notebook

            for notebook in notebooks:
                data = {
                    'action': 'set_default',
                    'type': keyword,
                    'notebookId': notebook['id']
                }
                name_prefix = "★ " if notebook['id'] == current_default_id else ""
                results.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name="%sSet as default %s notebook: %s" % (name_prefix, keyword, notebook['title']),
                    description="Notebook ID: %s" % notebook['id'],
                    on_enter=ExtensionCustomAction(data, keep_app_open=False)
                ))

        except Exception as e:
            results.append(ExtensionResultItem(
                icon='images/icon.png',
                name="⚠ Error Connecting to Joplin",
                description="Error: %s. Check server address and API token." % str(e),
                on_enter=HideWindowAction()
            ))

        return RenderResultListAction(results)


if __name__ == '__main__':
    JoplinExtension().run()
