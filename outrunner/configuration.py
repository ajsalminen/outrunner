import yaml
import os
import sys
from pkg_resources import resource_string

class Configuration(object):
    """Reads/writes the configuration and provides configuration related
    methods"""

    def __init__(self):
        package_name = __name__.split('.')[0]
        self._config_filename = "{}.conf.yml".format(package_name)
        self.load()

    def load(self):
        """Loads the configuration from a file.

        Configuration will be loaded from the user's home directory dotfile or
        from the default file provided by the program."""
        user = os.path.expanduser('~')
        user_config_path = "{}/.{}".format(user, self._config_filename)
        print(self._config_filename)
        if os.path.isfile(user_config_path):
            file =  open( user_config_path, 'r')
            self.config = yaml.safe_load(file)
        else:
            default_config = resource_string(__name__, self._config_filename)
            self.config = yaml.safe_load(default_config)


    def __getitem__(self, name):
        """Allow easy access to configuration keys.

        The configuration keys are provided as as part of the configuration
        object for easy and concise access."""
        return self.config.__getitem__(name)


    def get_config_for_path(self, path):
        """Load the config for a path.

        Returns the path-specific config as requested. This is used for providing
        alternate task runner configurations for specific filesystem paths."""
        if path in self.config['path_config']:
            project_type = self.config['path_config'][path]
        else:
            project_type = 'default'
        return self.config['projects'][project_type]
