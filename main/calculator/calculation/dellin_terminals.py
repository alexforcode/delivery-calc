from configparser import ConfigParser
from urllib import request
import json


def get_file_url(appkey):
    url = 'https://api.dellin.ru/v3/public/terminals.json'
    header = {'Content-Type': 'application/json'}
    data = {'appkey': appkey}
    data = bytes(json.dumps(data), encoding='utf-8')

    req = request.Request(url, data, header)
    resp = request.urlopen(req)

    data = json.loads(resp.read().decode('utf-8'))

    return data['url']


def download_file(url, path_to_save):
    data = request.urlopen(url).read().decode()
    data = json.loads(data)

    with open(path_to_save, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4, sort_keys=False)


def main():
    config = ConfigParser()
    config.read('/home/alex/dev/py-projects/dj-login/main/assets/data/config.ini')
    file_url = get_file_url(config['dellin']['appkey'])
    download_file(file_url, config['paths']['terminal_v3'])


if __name__ == '__main__':
    main()
