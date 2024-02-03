#!/usr/bin/env python3

import functools
import json
import pathlib
import re
import urllib
import urllib.request

from pathlib import Path

repos = [
    ("https://api.github.com/repos/PortsMaster/PortMaster-Releases", 10),
    ("https://api.github.com/repos/PortsMaster/PortMaster-New", 1000),
    ("https://api.github.com/repos/PortsMaster-MV/PortMaster-Multiverse", 10),
    # ("https://api.github.com/repos/PortsMaster-MV/PortMaster-MV-New", 1000),
    ]


@functools.lru_cache(maxsize=512)
def name_cleaner(text):
    temp = re.sub(r'[^a-zA-Z0-9 _\-\.]+', '', text.strip().lower())
    return re.sub(r'[ \.]+', '.', temp)


def fetch_text(url):
    try:
        # Open the URL
        with urllib.request.urlopen(url) as response:
            # Read the content of the file
            file_content = response.read()

        # Decode the bytes to a string (assuming the file is in UTF-8 encoding)
        return file_content.decode('utf-8')

    except urllib.error.URLError as err:
        print(f"Unable to download {url}: {err}")
        return None

    except UnicodeDecodeError as err:
        return None


def fetch_json(url):
    text = fetch_text(url)
    if text is None:
        return None

    return json.loads(text)


def fetch_recent_data(raw_data, repo, latest=10):
    for i in range(1, 300):
        print(f"Fetching releases page {i} of {repo}.")
        temp_data = fetch_json(f'{repo}/releases?page={i}')

        if temp_data is None or len(temp_data) == 0:
            break

        for release in temp_data:
            tag_name = release['tag_name']

            if tag_name in raw_data['releases']:
                print(f"- Updating {tag_name}")
                latest -= 1
            else:
                print(f"- New Release {tag_name}")
                raw_data['releases'].append(tag_name)

            raw_data['release_data'][tag_name] = release_data = {}

            for asset in release['assets']:
                asset_name = name_cleaner(asset['name'])
                if not asset_name.endswith('.zip'):
                    continue

                if asset_name not in raw_data['ports']:
                    raw_data['ports'].append(asset_name)

                if asset['download_count'] == 0:
                    continue

                release_data[asset_name] = asset['download_count']

            if latest <= 0:
                return


def main():
    raw_stats_json = Path('port_stats_raw.json')
    stats_json = Path('port_stats.json')

    raw_data = {
        'ports': [],
        'releases': [],
        'release_data': {},
        }

    if raw_stats_json.is_file():
        print("Loaded Data.")
        with open(raw_stats_json, 'r') as fh:
            raw_data = json.load(fh)
    else:
        print("Starting Fresh.")

    for repo, latest in repos:
        fetch_recent_data(raw_data, repo, latest=latest)

    with open(raw_stats_json, 'w') as fh:
        json.dump(raw_data, fh, indent=4)

    port_stats = {
        'ports': {
            port_name: 0
            for port_name in raw_data['ports']},
        'total_downloads': 0,
        }

    for release in raw_data['releases']:
        for port_name in raw_data['ports']:
            port_stats['ports'][port_name] += raw_data['release_data'][release].get(
                port_name, 0)
            port_stats['total_downloads'] += raw_data['release_data'][release].get(
                port_name, 0)

    with open(stats_json, 'w') as fh:
        json.dump(port_stats, fh, sort_keys=True, indent=4)


if __name__ == '__main__':
    main()
