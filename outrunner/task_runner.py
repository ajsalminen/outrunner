import os
import subprocess
import logging
class TaskRunner(object):
    """Prepares and runs a task on change notifications."""

    def __init__(self, config):
        self._config = config

    def prepare(self, path):
        """Prepare the task runner for watch notifications.

        For example ctags needs to have a generated tag file present."""

        if not os.path.isfile(self._config['tagfiles'][0]):
            command = self._config['initial_run_command']
            # This can be a long process so don't check return value.
            subprocess.Popen(command)

            logger = logging.getLogger(__name__)
            logger.info('Ran initial run command: ' + " ".join(command))

    def update(self, files):
        """Run a update task for the provided list of files."""
        command = []
        count = len(files)
        if count > self._config['full_scan_threshold']:
            command = self._config['full_update_command']
            subprocess.check_output(command, stderr=subprocess.STDOUT)
        else:
            command = self._config['single_update_command']
            for file in files:
                command = command + [file]
            subprocess.check_output(command, stderr=subprocess.STDOUT)


        logger = logging.getLogger(__name__)
        logger.info('Ran task-runner command: ' + " ".join(command))
