import asyncio
from urllib.parse import urlparse
import aiohttp
import yaml
import random
import pandas as pd


class Download:
    @staticmethod
    def filter_url(url):
        # 去除链接多余参数
        if not url:
            return False
        url = urlparse(url)
        return f'{url.scheme}://{url.netloc}{url.path}'

    def __init__(self, object_path) -> None:
        self.object_path = object_path
        self.ua_list = self._get_ua_list()
        self.data = pd.DataFrame()

    def _get_ua_list(self, ):
        path = f"{self.object_path}ua.yml"
        with open(path, 'r', encoding='utf-8') as f:
            ua_list = yaml.load(f, Loader=yaml.CLoader)
        return ua_list

    async def async_download_url(self, url, params=None, headers=None):
        headers = headers or random.choice(self.ua_list)
        try:
            async with self.session.get(url,
                                        params=params,
                                        headers=headers,
                                        timeout=6) as resp:
                status = resp.status
                assert status == 200
                # aiohttp不需要手动编码
                # encoding = cchardet.detect(resp.content)['encoding']
                # resp.encoding = encoding
                html = await resp.text()
                redirected_url = resp.url
        except Exception as e:
            msg = f'Failed download: {url} | exception: {str(type(e))}, {str(e)}'
            status = 0
            html = ''
            redirected_url = url
            print(msg)
        return status, html, url, redirected_url

    async def _async_get_resp(self, url_pool: dict, params):
        # 创建任务
        tasks = [
            self.async_download_url(k, params) for k, v in url_pool.items()
            if v
        ]
        return await asyncio.gather(*tasks)

    def _parse_resp(self, html_filter, url_pool: dict, resp):
        # 解包返回值
        for status, html, url, redirected_url in resp:
            # 解析网页
            df, next_urls = html_filter(html)
            self.data = pd.concat([self.data, df])  # 合并数据

            # 增加新链接
            for new_url in next_urls:
                new_url = self.filter_url(new_url)  # 格式化链接
                if new_url in url_pool:  # 去重
                    continue
                url_pool[new_url] = 1  # 标记新链接
            url_pool[url] = 0  # 标记已下载链接
        return url_pool

    async def async_fetch(self, html_filter, url_pool: dict, params):
        async with aiohttp.ClientSession() as self.session:
            count = 0
            while any(url_pool.values()):
                resp = await self._async_get_resp(url_pool, params)  # 下载并返回网页
                url_pool = self._parse_resp(html_filter, url_pool,
                                            resp)  # 解析网页

                count += len(resp)
                print(f"已下载第{count}页")
                await asyncio.sleep(6)  # 延迟访问，太快会触发访问限制，需要手动进网页输入验证
        return self.data
