from gavel.constants import DEFAULT_WELCOME_MESSAGE
import os
import yaml

BASE_DIR = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(BASE_DIR, '..', 'config.yaml')

class Config(object):

    def __init__(self, config_file):
        if not os.environ.get('IGNORE_CONFIG_FILE', False):
            with open(config_file) as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = {}

    # checks for an environment variable first, then an entry in the config file,
    # and then falls back to default
    def get(self, name, env_names=None, default=None):
        setting = None
        if env_names is not None:
            if not isinstance(env_names, list):
                env_names = [env_names]
            for env_name in env_names:
                setting = os.environ.get(env_name, None)
                if setting is not None:
                    break
        if setting is None:
            setting = self._config.get(name, None)
        if setting is None:
            if default is not None:
                return default
            else:
                raise LookupError('Cannot find value for setting %s' % name)
        return setting

config = Config(CONFIG_FILE)

# note: this should be kept in sync with 'config.sample.yaml' and
# 'config.vagrant.yaml'
ADMIN_PASSWORD = config.get('admin_password', 'ADMIN_PASSWORD')
DB_URI = config.get('db_uri', ['DATABASE_URL', 'DB_URI'], default='postgresql://localhost/gavel')
SECRET_KEY = config.get('secret_key', 'SECRET_KEY')
PORT = int(config.get('port', 'PORT', default=5000))
MIN_VIEWS = int(config.get('min_views', 'MIN_VIEWS', default=2))
WELCOME_MESSAGE = config.get('welcome_message', default=DEFAULT_WELCOME_MESSAGE)
