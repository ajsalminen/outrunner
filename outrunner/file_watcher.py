import subprocess
import os
import json
import copy
import logging

class WatchCommandError(Exception):
    """Thrown when a command used to set up watches fails."""
    pass

class FileWatcher(object):

    def __init__(self, config):
        self._config = config

    def watchman_command(self, command, data):
        """Helper method for issuing watchman commands.

        Provides error handling and loads the response from watchman."""
        if 'file_watcher_options' in self._config.config:
            command = command + self._config['file_watcher_options']
        result = subprocess.Popen(command, stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, errors) = result.communicate(data)

        if result.returncode != 0:
            raise WatchCommandError(errors)

        response = json.loads(output)
        if 'error' in response:
            message = 'Watchman returned error: {}'.format(response['error'])
            raise WatchCommandError(message)

        return response

    def watch(self, path):
        """Begin watching a directory for changes.

        The watched directory will generate separate notifications for creation
        and deletion events. These are delivered through calls to run_task()."""


        logger = logging.getLogger(__name__)
        logger.info("watch command called for: " + path)

        update_trigger = self._update_trigger(path)

        delete_trigger = self._delete_trigger(path)

        logger.debug("Update trigger is: " + json.dumps(update_trigger))
        logger.debug("Delete trigger is: " + json.dumps(delete_trigger))

        self.watchman_command(['watchman', 'watch', path], None)
        self.watchman_command(["watchman", "-j"], json.dumps(update_trigger))
        self.watchman_command(["watchman", "-j"], json.dumps(delete_trigger))



    def unwatch(self, path):
        """Stop watching a directory for changes."""
        self.watchman_command(['watchman', 'watch-del', path], None)

    def process_notification(self, notification):
        """Process a notification of changed files.

        The notification is transformed into a list of file names and
        returned."""

        files = []
        for line in notification:
            files.append(line.rstrip('\n'))
        return files


    def _match_restrictions(self, path):
        """Create rules about what files should be watched by watchman.

        Create the part of the wachman query that limits files watched based on
        extension and so on. At a minimum this will exclude the files that the
        task runner manages."""
        pattern_groups = []



        project_config = self._config.get_config_for_path(os.getcwd())

        extensions = project_config['extensions']
        patterns = []
        if extensions:
            for pattern in extensions:
                patterns.append(['match', pattern])
            pattern_groups.append(["anyof"] + patterns)

        patterns = []
        for name in project_config['task_runner']['tagfiles']:
            patterns.append(name)
        pattern_groups.append(["not", ["name", patterns]])

        patterns = []
        for pattern in project_config['task_runner']['exclude']:
            patterns.append(['match', pattern])
        pattern_groups.append(["not", ["anyof"] + patterns])

        expression = pattern_groups
        return expression

    def _base_trigger(self):
        """Define a base template for the watchman triggers."""
        trigger_template = {
            "stdin": "NAME_PER_LINE",
            "append_files": False,
            "command": self._config['tag_process_command'],
            "expression":
            ["allof",
             ["type", "f"]
         ]
        }
        return trigger_template


    def _update_trigger(self, path):
        """Create the configuration for the update trigger for a path."""
        trigger_wrap = ["trigger", path ]
        patterns = self._match_restrictions(path)

        update_trigger = self._base_trigger()
        update_trigger['expression'] += [['exists']] + patterns
        update_trigger['name'] = 'tags_update:' + path
        update_trigger['command'].append('update')
        update_trigger =  trigger_wrap + [update_trigger]
        return update_trigger

    def _delete_trigger(self, path):
        """Create the configuration for a delete trigger for a path."""
        trigger_wrap = ["trigger", path ]
        patterns = self._match_restrictions(path)

        delete_trigger = self._base_trigger()
        delete_trigger['expression'] += [['not', 'exists']] + patterns
        delete_trigger['name'] = 'tags_delete:' + path
        delete_trigger['command'].append('delete')
        delete_trigger = trigger_wrap + [delete_trigger]
        return delete_trigger
