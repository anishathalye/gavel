<img src="https://raw.githubusercontent.com/anishathalye/assets/master/gavel/banner.png" width="450" alt="Gavel banner">

**Gavel** is a project expo judging system.

Gavel was originally built for HackMIT and first used at HackMIT 2015. It has
been used by [dozens][users] of other events since then.

**If you use Gavel for your event, please add yourself to [this list][users]!
It only takes a minute, and knowing that Gavel is helping real events helps
keep us going <3**

## Demo

<p align="center">
    <a href="http://www.anishathalye.com/2016/09/19/gavel-an-expo-judging-system/">
        <img src="https://raw.githubusercontent.com/anishathalye/assets/master/gavel/screenshot.png" width="320" alt="Gavel screenshot">
    </a>
</p>

See the demo video
[here](http://www.anishathalye.com/2016/09/19/gavel-an-expo-judging-system/)!

## Users

See [here][users] for a list of events that have used Gavel in the past.

**If you use Gavel for your event, please add yourself to the list! It only
takes a minute, and knowing that Gavel is helping real events helps keep us
going <3**

and adding yourself to the list helps keep me motivated to continue
working on the software :)

## Design

Gavel is based on the method of pairwise comparisons. Before you use Gavel,
it's *highly recommended* that you read about the philosophy behind the
implementation as well as hints on how to use it in practice. Read [this blog
post][blog-1] first, and then read [this blog post][blog-2].

## Status

Gavel is stable software. We've used it successfully at HackMIT, and a bunch of
other hackathons and events have used it too.

Gavel is a pretty different way of doing judging. If you want to use this for
your hackathon or event, we highly recommend that you:

* Deploy it and play around with it ahead of time to get a feel for how the
  system works
* Read the blog posts linked above to get an idea of how to structure the
  judging process

If you have any questions, feel free to [email me][email].

If you're able to contribute to making Gavel better, that would be **awesome**!
We'd really appreciate any kind of input, especially pull requests.

## Deployment

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/mfalbers/gavel/tree/master)

The latest stable version is the `master` branch (and it's signed and tagged).
Development happens in the `develop` branch.

The web application is written in **Python 3** using Flask. It also uses NumPy
and SciPy for math stuff. Doing a `pip --no-cache-dir install -r requirements.txt` should
install all the dependencies.

The application uses Postgres for the database, so you need to have that on
your server. You need to create a database, which you can do with `createdb
gavel` (unless you're using a different database name). Before you use the app,
you need to initialize the database by running `python initialize.py`. **Note
that Gavel does not preserve database schema compatibility between versions.**

In order to send emails, you'll need to install Redis.

When testing, you can run the app with `python runserver.py`.

In production, you should use something like [Gunicorn][gunicorn] to serve
this. You can run the app with `gunicorn -b :<PORT> -w <number of workers>
gavel:app`. This is sufficient if you want to serve Gavel under its own domain
(e.g. `judging.example.com`). If you are serving Gavel under a subpath, e.g.
`example.com/judging`, you need to set the `SCRIPT_NAME` environment variable
(e.g. by passing `-e SCRIPT_NAME=/judging` to Gunicorn). If you are running
Gavel behind a proxy server, be sure to set `PROXY=true` in Gavel's settings.

For sending emails, you'll also need to start a celery worker with `celery -A
gavel:celery worker`.

## Configuration

Before starting the app, copy `config.template.yaml` to `config.yaml` and set
all the required settings (the ones that don't have default values).

Most settings can either be set in `config.yaml` or set as environment
variables. There's more detailed documentation in `config.template.yaml`.

If you don't want to use the config file and use only environment variables,
set the environment variable `IGNORE_CONFIG_FILE=true`.

## Troubleshooting

See the [troubleshooting
guide](https://github.com/anishathalye/gavel/wiki/Troubleshooting) in the Gavel
wiki.

## Use

To set up the system, use the admin interface on `/admin`. Log in with the
username `admin` and the password you set. Once you're logged in, you can input
information for all the projects and judges.

As you add judges, they'll automatically get emails with invitation links.
After that, the judging and ranking process is fully automated - the judge will
be able to read the welcome text, and then they'll be able to start judging.

The admin panel will rank projects in real time, ordered by their inferred
quality (Mu).

### Admin Panel Features

* If you want to (temporarily) close the judging system, click the "Close"
  button under "Global Settings"
* If you need to force re-send the invite email, use the "Email" button for the
  judge in the admin panel
* If you need to manually give a judge a login link, direct them to
  `/login/<secret>`
* If you want to send the next available judge to a certain project, use the
  "Prioritize" button
* If you need to deactivate projects or judges at any point, use the "Disable"
  button
* If a project hasn't been judged yet, you can delete it using the "Delete"
  button
* If a judge hasn't started yet, you can delete them using the "Delete" button
* If you need to see details for a project or judge, click on the item ID in
  the admin panel
    * If you need to edit a project (name, location, or description), you can
      do so on the item detail page
* If you want to sort the items in the admin panel, click on the table headers

## Development

Interested in hacking on Gavel? Awesome. See [DEVELOPMENT.md][development] for
a dev setup guide.

## Notes

If you do end up using this for your competition or hackathon, I would love to
hear about how it goes.

If anyone has questions, feel free to email Anish (me@anishathalye.com).

## Contributing

Do you have a feature request, bug report, or patch? Great! See
[CONTRIBUTING.md][contributing] for information on what you can do about that.

## Citation

If you use Gavel in any way in academic work, please cite the following:

```bibtex
@misc{athalye2016gavel,
  author = {Anish Athalye},
  title = {Gavel},
  year = {2016},
  howpublished = {\url{https://github.com/anishathalye/gavel}},
}
```

## License

Copyright (c) Anish Athalye. Released under AGPLv3. See
[LICENSE.txt][license] for details.

[blog-1]: http://www.anishathalye.com/2015/03/07/designing-a-better-judging-system/
[blog-2]: http://www.anishathalye.com/2015/11/09/implementing-a-scalable-judging-system/
[issues]: https://github.com/anishathalye/gavel/issues
[contributing]: CONTRIBUTING.md
[license]: LICENSE.txt
[development]: DEVELOPMENT.md
[email]: mailto:me@anishathalye.com
[gunicorn]: http://gunicorn.org/
[users]: https://github.com/anishathalye/gavel/wiki/Users
