#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

from urllib.parse import urlencode

import requests


OWNER = 'mozilla-services'
REPO = 'buildhub'

VALID_ENVIRONMENTS = ('stage', 'prod')
VALID_TASKS = ('cron', 'lambda', 'both')

QA_CONTACT = 'chartjes@mozilla.com'


def main(
    environment,
    task,
    tag=None,
    dry_run=False,
):
    if environment == 'stage':
        print("""
⚠️  NOTE! ⚠️

Stage is automatically upgraded (both cron and Lambda) when a new GitHub
release is made. Are you sure you need this bug?
        """)
        if not input("Sure? [y/N] ").strip().lower() in ('yes', 'y'):
            print("Thought so.")
            return 5

    api_url = f'https://api.github.com/repos/{OWNER}/{REPO}/releases'
    if not tag:
        api_url += '/latest'
    else:
        api_url += f'/tags/{tag}'
    response = requests.get(api_url)
    response.raise_for_status()
    release_info = response.json()

    # Prepare some variables for the string templates
    release_url = release_info['html_url']
    lambda_asset_url = None
    for asset in release_info['assets']:
        lambda_asset_url = asset['browser_download_url']
    env = environment.title()
    release_tag_name = release_info['tag_name']

    if task == 'lambda':
        summary = f"On {env}, please deploy Buildhub Lambda function {release_tag_name}"  # noqa
        comment = f"""
            Could you please update the Lambda function for Buildhub {env} with the following one?

            {release_url}

            {lambda_asset_url}

            Thanks!
        """  # noqa
    elif task == 'cron':
        summary = f"On {env}, please deploy Buildhub Cron function {release_tag_name}"  # noqa
        comment = f"""
            Could you please update the Cron function for Buildhub {env} with the following one?

            {release_url}

            Thanks!
        """  # noqa
    else:
        summary = f"On {env}, please deploy Buildhub Cron and Lambda function {release_tag_name}"  # noqa
        comment = f"""
            Could you please update the Cron *and* Lambda function for Buildhub {env} with the following one?

            {release_url}

            {lambda_asset_url}

            Thanks!
        """  # noqa

    comment = '\n'.join(x.strip() for x in comment.strip().splitlines())
    params = {
        'qa_contact': QA_CONTACT,
        'comment': comment,
        'short_desc': summary,
        'component': 'Operations: Storage',
        'product': 'Cloud Services',
        'bug_file_loc': release_url,
    }
    URL = 'https://bugzilla.mozilla.org/enter_bug.cgi?' + urlencode(params)
    print('To file this bug, click (or copy) this URL:')
    print('👇')
    print(URL)
    print('👆')
    return 0


if __name__ == '__main__':
    import argparse

    def check_environment(value):
        value = value.strip()
        if value not in VALID_ENVIRONMENTS:
            raise argparse.ArgumentTypeError(
                f'{value!r} not in {VALID_ENVIRONMENTS}'
            )
        return value

    def check_task(value):
        value = value.strip()
        if value not in VALID_TASKS:
            raise argparse.ArgumentTypeError(
                f'{value!r} not in {VALID_TASKS}'
            )
        return value

    parser = argparse.ArgumentParser(
        description='Deploy Buildhub (by filing Bugzilla bugs)!'
    )
    parser.add_argument(
        '-t', '--tag', type=str,
        help=(
            f'Name of the release (e.g. "v1.2.0"). If ommitted will be looked '
            f'on GitHub at https://github.com/{OWNER}/{REPO}/releases'
        )
    )

    parser.add_argument(
        '-e', '--environment',
        type=check_environment,
        default='prod',
        help="Environment e.g. 'stage' or 'prod'. (Default 'prod')"
    )
    parser.add_argument(
        'task', help='cron or lambda or both', type=check_task,
    )
    parser.add_argument('-d', '--dry-run', action='store_true')
    args = parser.parse_args()
    args = vars(args)
    main(args.pop('environment'), args.pop('task'), **args)
