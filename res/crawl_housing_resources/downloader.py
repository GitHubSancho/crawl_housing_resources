import requests
import yaml
import random
import cchardet


class Download:
    def __init__(self, object_path) -> None:
        self.object_path = object_path
        self.ua_list = self._get_ua_list()
        self.session = requests.Session()

    def _get_ua_list(self, ):
        path = f"{self.object_path}ua.yml"
        with open(path, 'r', encoding='utf-8') as f:
            ua_list = yaml.load(f, Loader=yaml.CLoader)
        return ua_list

    def download_url(self, url, params=None, headers=None):
        headers = headers or random.choice(self.ua_list)
        try:
            with self.session as s:
                resp = s.get(url, params=params, headers=headers)
                status = resp.status_code
                encoding = cchardet.detect(resp.content)['encoding']
                resp.encoding = encoding
                html = resp.text
                redirected_url = resp.url
        except Exception as e:
            msg = f'Failed download: {url} | exception: {str(type(e))}, {str(e)}'
            status = 0
            html = ''
            redirected_url = url
            print(msg)
        return status, html, url, redirected_url