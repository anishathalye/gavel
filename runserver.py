# Copyright (c) 2015-2016 Anish Athalye (me@anishathalye.com)
#
# This software is released under AGPLv3. See the included LICENSE.txt for
# details.

if __name__ == '__main__':
    from gavel import app
    from gavel.settings import PORT
    import os

    if os.environ.get('DEBUG', False):
        app.debug = True
    port = PORT
    app.run(host='0.0.0.0', port=port)
