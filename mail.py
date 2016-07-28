#!/usr/bin/env python
import os
from email.utils import formataddr

import requests

MAILGUN_MESSAGES_API_URL = 'https://api.mailgun.net/v3/{domain}/messages'
SENDER_IDENTITY = ('HackMIT Judging', 'judging-noreply@{domain}')
JUDGE_INVITE_TITLE = 'HackMIT Juding System Access'
JUDGE_INVITE_TEMPLATE = """Dear {judge_name},

Welcome to HackMIT judging! This email contains your magic link to the judging system.
If you are no longer judging, please do NOT access this link as it will affect judging results.
DO NOT SHARE your magic link with others - it is associated with your email address, and it's one account per person.
Judging will be explained during the judging orientation. Please do not open the link until then.

You may sign in to judging by accessing the following link: {magic_link} .

All questions should be directed to HackMIT organizers. Please do not reply to this automatic email.

HackMIT Team


(You are receiving this email because you are a judge at this event. If you do not want to receive further judging-related emails, please contact the organizers.)
"""


class MailgunRequestException(Exception):
    """Unsuccessful Mailgun HTTP request."""
    pass


def send_judge_email(judge_name, judge_address, magic_link):
    """Create email and send it through Mailgun.

    Arguments:
        judge_name (str): Full name of the judge.
        judge_address (str): Email address of the judge.
        magic_link (str): URL-escaped magic link for access.
    Returns:
        True if sent successfully, False if not.
    """
    if not os.environ.get('MAILGUN_DOMAIN') or not os.environ.get(
            'MAILGUN_API_KEY'):  # Require Mailgun credentials.
        raise ValueError(
            'Email: Environmental variables MAILGUN_DOMAIN and MAILGUN_API_KEY must be provided for outbound email.')

    from_name, from_email = SENDER_IDENTITY
    from_str = formataddr((from_name, from_email.format(
        domain=os.environ.get('MAILGUN_DOMAIN'))))  # "Name <a@b.c>" format
    to_str = formataddr((judge_name, judge_address))
    message_text = JUDGE_INVITE_TEMPLATE.format(judge_name=judge_name,
                                                magic_link=magic_link)

    params = {'from': from_str,
              'to': to_str,
              'subject': JUDGE_INVITE_TITLE,
              'text': message_text}
    try:
        mailgun_send_request(
            os.environ.get('MAILGUN_DOMAIN'),
            os.environ.get('MAILGUN_API_KEY'), params)
        return True
    except MailgunRequestException as e:
        print(e)
        return False


def mailgun_send_request(domain, api_key, params):
    """Make a POST request to Mailgun's API.

    Arguments:
        domain (str): Domain name used for Mailgun.
        api_key (str): API key corresponding to the domain.
        params (str): Parameters passed on to the POST request.
    Returns:
        True if no exceptions occured, raises MailgunRequestException() in case
            of a non-successful status code.
    """
    url = MAILGUN_MESSAGES_API_URL.format(domain=domain)
    r = requests.post(url, auth=('api', api_key), data=params)
    if r.status_code != 200 or '"id"' not in r.text:
        raise MailgunRequestException('{status} {text}'.format(
            status=r.status_code, text=r.text))
    return True
