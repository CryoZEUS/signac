import logging
logger = logging.getLogger(__name__)

AUTH_NONE = 'none'
AUTH_SCRAM_SHA_1 = 'SCRAM-SHA-1'
AUTH_SSL = 'SSL'
AUTH_SSL_x509 = 'SSL-x509'

SUPPORTED_AUTH_MECHANISMS = [AUTH_NONE]
NOT_SUPPORTED_AUTH_MECHANISMS = [AUTH_SCRAM_SHA_1, AUTH_SSL, AUTH_SSL_x509]

def raise_unsupported_auth_mechanism(mechanism):
    msg = "Auth mechanism '{}' for snapshot creation and restoration currently not supported. Supported mechanisms: {}."
    raise ValueError(msg.format(mechanism, SUPPORTED_AUTH_MECHANISMS))

def dump_db(host, database, dst):
    import subprocess
    cmd = "mongodump --host {host} --db {database} --out {dst}"
    c = cmd.format(host = host, database = database, dst = dst)
    logger.debug("Trying to dump database with command: '{}'.".format(c))
    subprocess.check_output(c.split(), stderr = subprocess.STDOUT)

def restore_db(host, database, src):
    import subprocess
    cmd = "mongorestore --host {host} --db {database} {src}"
    c = cmd.format(host = host, database = database, src = src)
    logger.debug("Trying to restore database with command: '{}'.".format(c))
    subprocess.check_output(c.split(), stderr = subprocess.STDOUT)

#def dump_db_ssl(host, database, dst, cachain, cakey):
#    import subprocess
#    cmd = "mongodump --host {host} --db {database} --out {dst} --ssl --sslCAFile={cachain} --sslPEMKeyFile={cakey}"
#    c = cmd.format(
#        host = host, database = database, dst = dst, 
#        cachain = cachain, cakey = cakey)
#    logger.debug("Trying to dump database with command: '{}'.".format(c))
#    subprocess.check_output(c.split(), stderr = subprocess.STDOUT)
#
#def restore_db_ssl(host, database, src, cachain, cakey):
#    import subprocess
#    cmd = "mongorestore --host {host} --db {database} --ssl --sslCAFile={cachain} -sslPEMKeyFile={cakey} {src}"
#    c = cmd.format(
#        host = host, database = database, src = src,
#        cachain = cachain, cakey = cakey)
#    logger.debug("Trying to restore database with command: '{}'.".format(c))
#    subprocess.check_output(c.split(), stderr = subprocess.STDOUT)

def dump_db_from_config(config, dst):
    auth_mechanism = config['database_auth_mechanism']
    if auth_mechanism in (AUTH_NONE, AUTH_SCRAM_SHA_1):
        dump_db(
            host = config['database_host'],
            database = config['project'],
            dst = dst)
    elif auth_mechanism in (AUTH_SSL, AUTH_SSL_x509):
        raise_unsupported_auth_mechanism(auth_mechanism)
        #dump_db_ssl(
        #    host = config['database_host'],
        #    database = config['project'],
        #    dst = dst,
        #    cachain = config['database_ssl_ca_certs'],
        #    cakey = config['database_ssl_cakeypemfile'])
    else:
        raise_unsupported_auth_mechanism(auth_mechanism)

def restore_db_from_config(config, src):
    auth_mechanism = config['database_auth_mechanism']
    if auth_mechanism in (AUTH_NONE, AUTH_SCRAM_SHA_1):
        restore_db(
            host = config['database_host'],
            database = config['project'],
            src = src)
    elif auth_mechanism in (AUTH_SSL, AUTH_SSL_x509):
        raise_unsupported_auth_mechanism(auth_mechanism)
        #restore_db_ssl(
        #    host = config['database_host'],
        #    database = config['project'],
        #    src = src,
        #    cachain = config['database_ssl_ca_certs'],
        #    cakey = config['database_ssl_cakeypemfile'])
    else:
        raise_unsupported_auth_mechanism(auth_mechanism)

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
    It must be "yes" (the default), "no" or None (meaning
    an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    import sys
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower() if sys.hexversion < 0x03000000 else input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

# Usage example
#
#>>> query_yes_no("Is cabbage yummier than cauliflower?")
#Is cabbage yummier than cauliflower? [Y/n] oops
#Please respond with 'yes' or 'no' (or 'y' or 'n').
#Is cabbage yummier than cauliflower? [Y/n] y
#>>> True
def add_verbosity_argument(parser, default = 0):
    """Add a verbosity argument to parser.

    Note:
      The argument is '-v' or '--verbosity'.
      Add multiple '-v' arguments, e.g. '-vv' or '-vvv' to 
      increase the level of verbosity.

    Args:
      parser: A argparse object.
      default: The default level, defaults to 0.
    """
    parser.add_argument(
        '-v', '--verbosity',
        help = "Set level of verbosity.",
        action = 'count',
        default = default,
        )

def add_verbosity_action_argument(parser, default = 0):
    """Add a verbosity argument to parser.

    Note:
      The argument is '-v'.
      Add multiple '-v' arguments, e.g. '-vv' or '-vvv' to 
      increase the level of verbosity.

    Args:
      parser: A argparse object.
      default: The default level, defaults to 0.
    """
    parser.add_argument(
        '-v',
        default = 0,
        nargs = '?',
        action = VerbosityLoggingConfigAction,
        dest = 'verbosity',
        )

def set_verbosity_level(verbosity, default = None, increment = 10):
    """Set the verbosity level as a function of an integer level.

    Args:
      verbosity: The verbosity level as integer.
      default: The default verbosity level, defaults to logging.ERROR.
    """
    import logging
    if default is None:
        default = logging.ERROR
    logging.basicConfig(
        level = default - increment * verbosity)

import argparse
class VerbosityAction(argparse.Action):
    def __call__(self, parser, args, values, option_string = None):
        if values == None:
            values = '1'
        try:
            values = int(values)
        except ValueError:
            values = values.count('v') + 1
        setattr(args, self.dest, values)

class VerbosityLoggingConfigAction(VerbosityAction):
    def __call__(self, parser, args, values, option_string = None):
        super(VerbosityLoggingConfigAction, self).__call__(parser, args, values, option_string)
        import logging
        v_level = getattr(args, self.dest)
        set_verbosity_level(v_level)

class EmptyIsTrue(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values is None:
            values = True
        setattr(namespace, self.dest, values)

class SmartFormatter(argparse.HelpFormatter):

    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        return argparse.HelpFormatter._split_lines(self, text, width)