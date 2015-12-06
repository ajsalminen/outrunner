import cPickle
import os
import fcntl
import logging

class WatchManagerError(Exception):
    """Thrown when watchmanager fails."""
    pass


class WatchManager(object):
    """
    Keeps track of processes that set up watches.

    Multiple processes which are considered instances of clients such as shells
    and code editors can visit the same source code repositories. This class
    provides an interface through which they register a watch.
    """

    _watches = {}
    def __init__(self, task_runner, watcher):
        self._task_runner = task_runner
        self._watcher = watcher
        user = os.path.expanduser('~')
        self._state_file_path = "{}/.{}.state".format(user,  __name__.split('.')[0])
        self.load()


    def load(self):
        """Loads the current watch state from disk.

        The file is locked so multiple instances can run without data loss."""

        if os.path.isfile(self._state_file_path):
            self._watch_state_file = open(self._state_file_path, 'r+b')
            fcntl.lockf(self._watch_state_file, fcntl.LOCK_EX)
            # A just created file could be empty here and loading fail.
            # Would happen only for initial run and won't result in data loss.
            self._watches = cPickle.load(self._watch_state_file)
        else:
            # Only throws IOError if first run and trying to at the same time.
            # Replace with "x" open once python 2 is dead.
            fd = os.open(self._state_file_path, os.O_WRONLY|os.O_CREAT|os.O_EXCL)
            self._watch_state_file =  os.fdopen(fd, "w")
            fcntl.lockf(self._watch_state_file, fcntl.LOCK_EX)

    def save(self):
        """Saves the current watch state to disk.

        The lock that is placed on the file when opening is released here."""
        self._watch_state_file.seek(0)
        # Pickle dictionary using protocol 0.
        cPickle.dump(self._watches, self._watch_state_file)
        self._watch_state_file.close()

    def exists(self, path):
        """Check whether a watch exists for the path.

        Path should be complete. Returns True if the watch exists, False
        otherwise."""
        if path in self._watches:
            return True
        else:
            return False

    def add(self, pid, path):
        """Add a watch to a path for a process.

        The requested path is added to watched and the task runner can prepare
        it. The pid should be the process id that wants to set up a watch for
        path. Path should be complete."""
        logger = logging.getLogger(__name__)
        logger.info("Received request to watch {} for {}".format(path, pid))

        if path not in self._watches:
            self._task_runner.prepare(path)
            self._watcher.watch(path)
            self._watches[path] = { pid }
            try:
                self.save()
            except cPickle.PicklingError as e:
                # Remove the watch we just created if the state cannot be saved.
                logger.error("Saving watch state failed: {}".format(e))
                self._watcher.unwatch(path)
                raise WatchManagerError('Unable to save watch state.')
        else:
            self._watches[path].add(pid)



    def remove(self, pid, path):
        """Remove a process from watchers of a path.

        If there are no remaining processes that wish to watch the path, the
        watch on it will be stopped as well."""

        logger = logging.getLogger(__name__)
        logger.info("Received request to stop watching {} for {}".format(path, pid))

        if path in self._watches and pid in self._watches[path]:
            self._watches[path].remove(pid)

            if not self._watches[path]:
                logger = logging.getLogger(__name__)
                logger.info('No more watches for: ' + path)
                self._watches.pop(path, None)
                self._watcher.unwatch(path)
            try:
                self.save()
            except cPickle.PicklingError as e:
                # Readd the watch we just removed if the state cannot be saved.
                logger.error("Saving watch state failed: {}".format(e))
                self._watcher.watch(path)
                raise WatchManagerError('Unable to save watch state.')
