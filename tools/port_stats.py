#!/usr/bin/env python3

import functools
import json
import pathlib
import re

from pathlib import Path

import requests


@functools.lru_cache(maxsize=512)
def name_cleaner(text):
    temp = re.sub(r'[^a-zA-Z0-9 _\-\.]+', '', text.strip().lower())
    return re.sub(r'[ \.]+', '.', temp)


def fetch(url):
    r = requests.get(url)
    if r.status_code != 200:
        print(f"Failed to download {r.status_code}")
        return None

    return r


def fetch_json(url):
    r = fetch(url)
    if r is None:
        return None

    return r.json()


def fetch_recent_data(raw_data, latest=10):

    for i in range(1, 300):
        print(f"Fetching releases page {i}.")
        temp_data = fetch_json(f'https://api.github.com/repos/PortsMaster/PortMaster-Releases/releases?page={i}')

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

    fetch_recent_data(raw_data, latest=4)

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
            port_stats['ports'][port_name] += raw_data['release_data'][release].get(port_name, 0)
            port_stats['total_downloads'] += raw_data['release_data'][release].get(port_name, 0)

    with open(stats_json, 'w') as fh:
        json.dump(port_stats, fh, indent=4)


if __name__ == '__main__':
    main()
