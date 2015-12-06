from __future__ import print_function
import sys, os
import subprocess
import cPickle
import time
import logging
import logging.config
import yaml
from configuration import Configuration
from watch_manager import WatchManager, WatchManagerError
from file_watcher import FileWatcher, WatchCommandError
from task_runner import TaskRunner

def main():
    """The program entry point.

    Main method that sets up the controller for execution."""
    try:
        config = Configuration()
    except IOError as e:
        print("I/O error({0}): {1}".format(e.errno, e.strerror), file=sys.stderr)
        sys.exit(os.EX_IOERR)
    except yaml.YAMLError as e:
        print("Error in configuration file: {}".format(e), file=sys.stderr)
        sys.exit(os.EX.DATAERR)

    file_watcher = FileWatcher(config)
    project_config = config.get_config_for_path(os.getcwd())
    task_runner = TaskRunner(project_config['task_runner'])
    controller = MainController(config, task_runner, file_watcher)
    sys.exit(controller.run(sys.argv[1:]))

class MainController:
    """Controller class that handles commands.

    The main controller class that handles setting up the various components of
    the program and their dependencies and maps the commands and their arguments
    to the components that provide their functionality."""

    def __init__(self, config, task_runner, file_watcher):
        self._config = config
        self._file_watcher = file_watcher
        self._logger = self.setup_logging(config['logging'])
        self._task_runner = task_runner

    def setup_logging(self, config):
        """ Configures the logger."""
        logging.config.dictConfig(config)
        logger = logging.getLogger(__name__)
        return logger

    def run(self, command_arguments):
        """ The main method that determines the command being called."""
        if len(command_arguments) < 2:
            print("Invalid arguments.")
            return os.EX_USAGE

        command = command_arguments[0]
        method = None
        if command in ['watch', 'unwatch']:
            path = command_arguments[1]

            if len(command_arguments) > 2:
                parent = command_arguments[2]
            else:
                parent = os.getppid()
            method = getattr(self, command)

            try:
                method(path, parent)
            except WatchCommandError as e:
                self._logger.error(e)
                return os.EX_UNAVAILABLE
            except OSError as e:
                self._logger.error(e)
                return os.EX_UNAVAILABLE

        elif command == 'run_task':
            mode = command_arguments[1]
            method = getattr(self, command)
            try:
                method(mode)
            except OSError as e:
                self._logger.error(e)
                return os.EX_UNAVAILABLE

        if not method:
            print("Invalid arguments.")
            return os.EX_USAGE

        return os.EX_OK


    def run_task(self, mode):
        """Handles task runner commands.

        The command is typically called by the service that is configured to
        watch the filesystem and notify on select events."""
        self._logger.info("run_task called with arguments: " + " ".join(sys.argv[1:]) + "\n")
        self._logger.info("current working dir is: " + os.getcwd())

        start = time.clock()
        files = self._file_watcher.process_notification(sys.stdin)
        try:
            self._task_runner.update(files)
        except subprocess.CalledProcessError as e:
            self._logger.error("{}: {}".format(e, e.output))
            return os.EX_UNAVAILABLE
        except OSError as e:
            self._logger.error(e)
            return os.EX_UNAVAILABLE

        end = time.clock()
        self._logger.info("took: " + str(end - start) + ' seconds\n')

    def watch(self, path, parent):
        """Handles watch commands.

        A process that wishes to set up watches for a directory will issue a
        watch command. This sets up the watch if necessary."""
        self._logger.info("Watch command ran for {} by {}".format(path, parent))

        project_config = self._config.get_config_for_path(os.getcwd())

        try:
            watch_manager = WatchManager(self._task_runner, self._file_watcher)
        except IOError as e:
            self._logger.error("I/O error({0}): {1}".format(e.errno, e.strerror))
            return os.EX_IOERR
        except cPickle.UnpicklingError as e:
            return OS.EX_IOERR

        try:
            watch_manager.add(parent, path)
        except OSError as e:
            self._logger.error(e)
            return os.EX_UNAVAILABLE
        except WatchManagerError as e:
            return os.EX_IOERR

    def unwatch(self, path, parent):
        """Handles unwatch commands.

        A process that wishes to stop watching a directory will issue an
        unwatch command. This method removes the watch if necessary."""
        self._logger.info("Unwatch command ran for {} by {}".format(path, parent))

        try:
            watch_manager = WatchManager(self._task_runner, self._file_watcher)
        except IOError as e:
            self._logger.error("I/O error({0}): {1}".format(e.errno, e.strerror))
            return os.EX_IOERR
        except cPickle.UnpicklingError as e:
            return OS.EX_IOERR

        try:
            watch_manager.remove(parent, path)
        except OSError as e:
            self._logger.error(e)
            return os.EX_UNAVAILABLE
        except WatchManagerError as e:
            return os.EX_IOERR
