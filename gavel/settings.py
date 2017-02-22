import gavel.constants as constants
import os
import yaml

BASE_DIR = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(BASE_DIR, '..', 'config.yaml')

class Config(object):

    def __init__(self, config_file):
        if not _bool(os.environ.get('IGNORE_CONFIG_FILE', False)):
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

def _bool(truth_value):
    if isinstance(truth_value, bool):
        return truth_value
    if isinstance(truth_value, int):
        return bool(truth_value)
    if isinstance(truth_value, str):
        if truth_value.isnumeric():
            return bool(int(truth_value))
        lower = truth_value.lower()
        return lower.startswith('t') or lower.startswith('y') # accepts things like 'yes', 'True', ...
    raise ValueError('invalid type for bool coercion')

def _list(item):
    if isinstance(item, list):
        return item
    return [item]

c = Config(CONFIG_FILE)

# note: this should be kept in sync with 'config.template.yaml' and
# 'config.vagrant.yaml'
BASE_URL =            c.get('base_url',        'BASE_URL')
ADMIN_PASSWORD =      c.get('admin_password',  'ADMIN_PASSWORD')
DB_URI =              c.get('db_uri',          ['DATABASE_URL', 'DB_URI'], default='postgresql://localhost/gavel')
SECRET_KEY =          c.get('secret_key',      'SECRET_KEY')
PORT =            int(c.get('port',            'PORT',                     default=5000))
MIN_VIEWS =       int(c.get('min_views',       'MIN_VIEWS',                default=2))
TIMEOUT =       float(c.get('timeout',         'TIMEOUT',                  default=5.0)) # in minutes
WELCOME_MESSAGE =     c.get('welcome_message',                             default=constants.DEFAULT_WELCOME_MESSAGE)
CLOSED_MESSAGE =      c.get('closed_message',                              default=constants.DEFAULT_CLOSED_MESSAGE)
DISABLED_MESSAGE =    c.get('disabled_message',                            default=constants.DEFAULT_DISABLED_MESSAGE)
LOGGED_OUT_MESSAGE =  c.get('logged_out_message',                          default=constants.DEFAULT_LOGGED_OUT_MESSAGE)
WAIT_MESSAGE =        c.get('wait_message',                                default=constants.DEFAULT_WAIT_MESSAGE)
DISABLE_EMAIL = _bool(c.get('disable_email',   'DISABLE_EMAIL',            default=False))
EMAIL_HOST =          c.get('email_host',      'EMAIL_HOST',               default='smtp.gmail.com')
EMAIL_PORT =      int(c.get('email_port',      'EMAIL_PORT',               default=587))
EMAIL_FROM =          c.get('email_from',      'EMAIL_FROM')
EMAIL_USER =          c.get('email_user',      'EMAIL_USER')
EMAIL_PASSWORD =      c.get('email_password',  'EMAIL_PASSWORD')
EMAIL_AUTH_MODE =     c.get('email_auth_mode', 'EMAIL_AUTH_MODE',          default='tls').lower()
EMAIL_CC =      _list(c.get('email_cc',        'EMAIL_CC',                 default=[]))
EMAIL_SUBJECT =       c.get('email_subject',                               default=constants.DEFAULT_EMAIL_SUBJECT)
EMAIL_BODY =          c.get('email_body',                                  default=constants.DEFAULT_EMAIL_BODY)
SEND_STATS =    _bool(c.get('send_stats',      'SEND_STATS',               default=True))
