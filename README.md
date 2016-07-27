# Gavel

**Gavel** is a project expo judging system.

It was originally built for HackMIT and first used at HackMIT 2015. It's also
been used by a number of other hackathons.

[![Join the chat at https://gitter.im/anishathalye/gavel](https://badges.gitter.im/anishathalye/gavel.svg)](https://gitter.im/anishathalye/gavel?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

## Design

Gavel is based on the method of pairwise comparisons. Before you use Gavel,
it's *highly recommended* that you read about the philosophy behind the
implementation, as well as hints on how to use it in practice. Read [this blog
post][blog-1] first, and then read [this blog post][blog-2].

## Status

Gavel is currently **beta software**! We've used it successfully at HackMIT
2015, and a bunch of other hackathons have used it too, but it's still pretty
rough around the edges.

If you want to use this for your hackathon or event, we highly recommend that
you:

* Deploy it and play around with it ahead of time to get a feel for how the
  system works
* Take a look at the [issues][issues] to see the current state of affairs and
  learn about some things that might be nonintuitive
* Read the blog posts linked above to get a feel for how many judges you need

If you have any questions, feel free to [email me][email].

If you're able to contribute to making Gavel better, that would be **awesome**!
We'd really appreciate pull requests, and we'll include your name in our list
of [contributors][contributors] if you contribute any code to Gavel.

If you're interested in working closely with the HackMIT team to make this
software better, email us at team@hackmit.org and we can talk about how we can
work together!

## Deployment

The web application is written in Python using Flask. It also uses NumPy and
SciPy for math stuff. Doing a `pip install -r requirements.txt` should install
all the dependencies.

The application uses Postgres for the database, so you need to have that on
your server. You need to create a database, which you can do with `createdb
gavel` (unless you're using a different database name). Before you use the app,
you need to initialize the database by running `python initialize.py`.

When testing, you can run the app with `python gavel.py`. In production, you
should use something like [Gunicorn][gunicorn] to serve this. You can run the
app with `gunicorn gavel:app`.

## Configuration

Before starting the app, set the following environment variables:

* `ADMIN_PASSWORD`
* `SECRET_KEY` - set this to something random
* `SQLALCHEMY_DATABASE_URI` - you only need to set this if you're doing
  something nonstandard

## Use

Using the admin interface on `/admin`, input data for all the projects and
input information for all the judges.

After that, get the "magic link" to each of the judges. The judge should
navigate to `http://example.com/login/{secret}`. This is a bit clunky, and it
should be fixed soon: see [this
issue](https://github.com/anishathalye/gavel/issues/1) for details. After the
judges navigate to the secret link, they'll be prompted to go through projects
and judge them.

## Notes

If you do end up using this for your competition or hackathon, I would love to
hear about how it goes.

If anyone has questions, feel free to email Anish (me@anishathalye.com).

## Contributing

Do you have a feature request, bug report, or patch? Great! See
[CONTRIBUTING.md][contributing] for information on what you can do about that.
We'll include your name in our list of [contributors][contributors] if you
contribute any code to Gavel.

## License

Copyright (c) 2015-2016 Anish Athalye. Released under AGPLv3. See
[LICENSE.txt][license] for details.

If you're interested in getting access to this system under a different
license, please [contact me][email].

[blog-1]: http://www.anishathalye.com/2015/03/07/designing-a-better-judging-system/
[blog-2]: http://www.anishathalye.com/2015/11/09/implementing-a-scalable-judging-system/
[issues]: https://github.com/anishathalye/gavel/issues
[contributors]: CONTRIBUTORS.md
[contributing]: CONTRIBUTING.md
[license]: LICENSE.txt
[email]: mailto:me@anishathalye.com
[gunicorn]: http://gunicorn.org/
