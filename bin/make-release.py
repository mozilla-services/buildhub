#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import os
import datetime
import re
import subprocess
import time
import pkg_resources

import requests
from decouple import config

OWNER = 'mozilla-services'
REPO = 'buildhub'

GITHUB_API_KEY = config('GITHUB_API_KEY', default='')


def _format_age(seconds):
    seconds = int(seconds)
    if seconds > 3600:
        return '{} hours {} minutes ago'.format(
            seconds // 3600,
            round(seconds % 3600 / 60),
        )
    elif seconds > 60:
        return '{} minutes {} seconds ago'.format(
            seconds // 60,
            round(seconds % 60),
        )
    else:
        return '{} seconds ago'.format(seconds)


def _format_file_size(bytes):
    if bytes > 1024 * 1024:
        return '{:.1f}MB'.format(bytes / 1024 / 1024)
    elif bytes > 1024:
        return '{:.1f}KB'.format(bytes / 1024)
    else:
        return '{}B'.format(bytes)


def check_output(*args, **kwargs):
    if len(args) == 1:
        if isinstance(args[0], str):
            args = args[0].split()
        else:
            args = args[0]
    return subprocess.check_output(args, **kwargs).decode('utf-8').strip()


def main(
    part,
    dry_run=False,
    github_api_key=None,
    tag_name_format='v{version}',
    upstream_name='master',
):
    github_api_key = github_api_key or GITHUB_API_KEY
    assert github_api_key, 'GITHUB_API_KEY or --github-api-key not set.'

    # If this 401 errors, go here to generate a new personal access token:
    # https://github.com/settings/tokens
    # Give it all the 'repos' scope.
    api_url = 'https://api.github.com/user'
    response = requests.get(api_url, headers={
        'Authorization': 'token {}'.format(github_api_key)
    })
    response.raise_for_status()

    # Before we proceed, check that the `lambda.zip` is up to date.
    lambda_mtime = os.stat('lambda.zip').st_mtime
    age = time.time() - lambda_mtime
    print("The lambda.zip...\n")
    dt = datetime.datetime.fromtimestamp(lambda_mtime)
    print('\tLast modified:', dt.strftime('%d %B %Y - %H:%M:%S'))
    print('\tAge:', _format_age(age))
    print('')
    try:
        ok = input('Is this lambda.zip recently generated? [Y/n] ')
    except KeyboardInterrupt:
        print('\n\nTip! Generate it by running: make lambda.zip ')
        return 3
    if ok.lower().strip() == 'n':
        print('Tip! Generate it by running: make lambda.zip ')
        return 3

    # Figure out the current version
    current_version = pkg_resources.get_distribution('buildhub').version
    z, y, x = [int(x) for x in current_version.split('.')]
    if part == 'major':
        next_version = (z + 1, 0, 0)
    elif part == 'minor':
        next_version = (z, y + 1, 0)
    else:
        next_version = (z, y, x + 1)
    next_version = '.'.join(str(n) for n in next_version)

    # Figure out the CHANGELOG

    # Let's make sure we're up-to-date
    current_branch = check_output('git rev-parse --abbrev-ref HEAD')
    if current_branch != 'master':
        # print("WARNING, NOT ON MASTER BRANCH")# DELETE WHEN DONE HACKING
        print("Must be on the master branch to do this")
        return 1

    # The current branch can't be dirty
    try:
        subprocess.check_call(
            'git diff --quiet --ignore-submodules HEAD'.split()
        )
    except subprocess.CalledProcessError:
        print(
            "Can't be \"git dirty\" when we're about to git pull. "
            "Stash or commit what you're working on."
        )
        return 2

    # Make sure we have all the old git tags
    check_output(
        f'git pull {upstream_name} master --tags',
        stderr=subprocess.STDOUT
    )

    # We're going to use the last tag to help you write a tag message
    last_tag, last_tag_message = check_output([
        'git',
        'for-each-ref',
        '--sort=-taggerdate',
        '--count=1',
        '--format',
        '%(tag)|%(contents:subject)',
        'refs/tags'
    ]).split('|', 1)

    commits_since = check_output(f'git log {last_tag}..HEAD --oneline')
    commit_messages = []
    for commit in commits_since.splitlines():
        wo_sha = re.sub('^[a-f0-9]{7} ', '', commit)
        commit_messages.append(wo_sha)

    print(' NEW CHANGE LOG '.center(80, '='))
    change_log = []
    head = '{} ({})'.format(
        next_version,
        datetime.datetime.now().strftime('%Y-%m-%d')
    )
    head += '\n{}'.format('-' * len(head))
    change_log.append(head)
    change_log.extend(['- {}'.format(x) for x in commit_messages])
    print('\n\n'.join(change_log))
    print('=' * 80)

    assert commit_messages

    # Edit jobs/setup.py
    with open('jobs/setup.py') as f:
        setup_py = f.read()
    assert "version='{}',".format(current_version) in setup_py
    setup_py = setup_py.replace(
        "version='{}',".format(current_version),
        "version='{}',".format(next_version),
    )
    if not dry_run:
        with open('jobs/setup.py', 'w') as f:
            f.write(setup_py)

    # Edit jobs/CHANGELOG.rst
    with open('jobs/CHANGELOG.rst') as f:
        original = f.read()
    assert '\n\n'.join(change_log) not in original
    new_change_log = original.replace(
        '=========',
        '=========\n\n{}\n\n'.format(
            '\n\n'.join(change_log)
        )
    )
    if not dry_run:
        with open('jobs/CHANGELOG.rst', 'w') as f:
            f.write(new_change_log)

    # Actually commit this change.
    commit_message = f'Bump {next_version}'
    if dry_run:
        print('git add jobs/CHANGELOG.rst jobs/setup.py')
        print(
            f'git commit -m "{commit_message}"'
        )
    else:
        subprocess.check_call([
            'git', 'add', 'jobs/CHANGELOG.rst', 'jobs/setup.py',
        ])
        subprocess.check_call([
            'git', 'commit', '-m', commit_message,
        ])

    # Commit these changes
    tag_name = tag_name_format.format(version=next_version)
    tag_body = '\n\n'.join(['- {}'.format(x) for x in commit_messages])
    if dry_run:
        print(
            f'git tag -s -a {tag_name} -m "...See CHANGELOG output above..."'
        )
    else:
        subprocess.check_call([
            'git',
            'tag',
            '-s',
            '-a', tag_name,
            '-m', tag_body,
        ])

    # Let's push this now
    if dry_run:
        print(f'git push {upstream_name} master --tags')
    else:
        subprocess.check_call(
            f'git push {upstream_name} master --tags'.split()
        )

    if not dry_run:
        release = _create_release(
            github_api_key,
            tag_name,
            tag_body,
            name=tag_name,
        )
        asset_info = _upload_lambda_zip(
            github_api_key,
            release['upload_url'],
            release['id'],
            f'buildhub-lambda-{tag_name}.zip',
        )
        print('Build asset uploaded.')
        print('Can be downloaded at:')
        print(asset_info['browser_download_url'])

        print('\n')
        print(' 🎉  ALL DONE! 🎊 ')
        print('\n')

    return 0


def _create_release(github_api_key, tag_name, body, name=''):
    api_url = (
        f'https://api.github.com'
        f'/repos/{OWNER}/{REPO}/releases'
    )
    response = requests.post(
        api_url,
        json={
            'tag_name': tag_name,
            'body': body,
            'name': name,
        }, headers={
            'Authorization': 'token {}'.format(github_api_key)
        }
    )
    response.raise_for_status()
    return response.json()


def _upload_lambda_zip(github_api_key, upload_url, release_id, filename):
    upload_url = upload_url.replace(
        '{?name,label}',
        f'?name={filename}',
    )
    print('Uploading lambda.zip as {} ({})...'.format(
        filename,
        _format_file_size(os.stat('lambda.zip').st_size)
    ))
    with open('lambda.zip', 'rb') as f:
        response = requests.get(
            upload_url,
            data=f,
            headers={
                'Content-Type': 'application/zip',
                'Authorization': 'token {}'.format(github_api_key)
            },
        )
    response.raise_for_status()
    return response.json()


if __name__ == '__main__':
    import sys
    import argparse
    parser = argparse.ArgumentParser(description='Release Buildhub!')
    parser.add_argument('part', type=str, help='major, minor or patch')
    parser.add_argument('-d', '--dry-run', action='store_true')
    parser.add_argument(
        '-g', '--github-api-key',
        help='GitHub API key unless set by GITHUB_API_KEY env var.'
    )
    parser.add_argument(
        '-u', '--upstream-name',
        help=(
            'Name of the git remote origin to push to. Not your fork. '
            'Defaults to "origin".'
        ),
        default='origin',
    )
    args = parser.parse_args()
    if args.part not in ('major', 'minor', 'patch'):
        parser.error("invalid part. Must be 'major', 'minor', or 'patch'")
    args = vars(args)
    sys.exit(main(args.pop('part'), **args))
