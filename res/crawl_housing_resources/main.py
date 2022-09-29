#!/usr/bin/env python
#-*- coding: utf-8 -*-
#FILE: main.py
#CREATE_TIME: 2022-09-07
#AUTHOR: Sancho
"""
爬取互联网上的住房信息
"""

import sys
from time import sleep
from urllib.parse import urlparse
import pandas as pd
from requests import RequestException
import webbrowser
import aiohttp
import asyncio
# ----
from resources_manager import ResourcesBase, Anjuke
from downloader import Download
from app import app

# pandas输出设置项
pd.set_option('display.unicode.ambiguous_as_wide', True)  #处理数据的列标题与数据无法对齐的情况
pd.set_option('display.unicode.east_asian_width', True)  #无法对齐主要是因为列标题是中文


class Engine:
    def __init__(self) -> None:
        pass

    def start(self, *args, **kwargs):
        # 判断传参格式,实例化房源类
        self._instantiation_instance(*args, **kwargs)

        # 下载和解析页面
        self.downloader = Download(OBJECT_PATH)  # 初始化下载器
        self.url = self.instance.build_url()  # 在房源类中格式化url
        self.params = self.instance.build_params()  # 在房源类中格式化参数
        data = self._next_pages()

        # 显示结果
        self._open_html(data)

    async def async_start(self, *args, **kwargs):
        # 判断传参格式,实例化房源类
        self._instantiation_instance(*args, **kwargs)

        # 下载和解析页面
        self.downloader = Download(OBJECT_PATH)  # 初始化下载器
        self.url = self.instance.build_url()  # 在房源类中格式化url
        self.params = self.instance.build_params()  # 在房源类中格式化参数
        data = await self._async_next_pages()

        # 显示结果
        self._open_html(data)

    def _open_html(self, data: pd.DataFrame):
        name = '租房收集.csv'
        data.to_csv(name, index=False, encoding='utf_8_sig')
        webbrowser.open('http://127.0.0.1:5000/')
        app.run()

    def _instantiation_instance(self, *args, **kwargs):
        if not isinstance(args, tuple) and hasattr(args, '__call__'):
            # 只有一个参数，且是可执行的类，直接实例化
            self.fun = args
            self.instance: ResourcesBase = self.fun()
        elif hasattr(args[0], '__call__'):
            # 第一个参数是可执行的类，实例化时传入参数
            self.fun = args[0]
            self.instance: ResourcesBase = self.fun(*args[1:], **kwargs)
        else:
            raise f"请正确输入房源类：{args}"

    def _filter_html(self, status, html):
        if status != 200:
            raise RequestException
        return self.instance.filter_html(html)

    def _filter_url(self, url):
        if not url:
            return False
        url = urlparse(url)
        return f'{url.scheme}://{url.netloc}{url.path}'

    def _next_pages(self):
        count = 1
        next_url = self.url
        params = self.params
        data = pd.DataFrame()
        while next_url:
            status, html, url, redirected_url = self.downloader.download_url(
                next_url, params)
            df, next_url = self._filter_html(status, html)
            data = pd.concat([data, df])
            next_url = self._filter_url(next_url)

            print(f"第{count}页")
            count += 1
            sleep(6)  # 延迟访问，太快会触发访问限制，需要手动进网页输入验证
        return data

    async def _get_tasks(self, session, params):
        tasks = [
            self.downloader.async_download_url(session, k, params)
            for k, v in self.url_pool.items() if v
        ]
        return await asyncio.gather(*tasks)

    def _unpack_resp(self, resp):
        # 解包返回值
        for status, html, url, redirected_url in resp:
            # 解析网页
            df, next_urls = self._filter_html(status, html)
            self.data = pd.concat([self.data, df])  # 合并数据

            # 格式化链接
            # [
            #     self.url_pool.update({self._filter_url(_url): 1})
            #     for _url in next_urls if not self.url_pool.get(url, False)
            # ]  # 增加新链接
            for _url in next_urls:  # 增加新链接
                _url = self._filter_url(_url)
                if _url in self.url_pool.keys():
                    continue
                self.url_pool.update({_url: 1})
            self.url_pool[url] = 0  # 标记已下载链接

    async def _async_next_pages(self):
        count = 0
        params = self.params
        self.data = pd.DataFrame()
        self.url_pool = {self.url: 1}  # 创建链接池,1=待访问，0=已完成
        async with aiohttp.ClientSession() as session:
            while any(self.url_pool.values()):
                resp = await self._get_tasks(session, params)
                self._unpack_resp(resp)

                count += len(resp)
                print(f"第{count}页")
                await asyncio.sleep(6)  # 延迟访问，太快会触发访问限制，需要手动进网页输入验证
        return self.data


def get_path():
    # 根据操作系统找到当前文件路径
    if sys.platform == "win32":
        p = '\\'
    else:
        p = '/'
    my_path = sys.path[0]
    object_path = f'{my_path}{p}..{p}..{p}'
    return my_path, object_path


if __name__ == "__main__":
    MY_PATH, OBJECT_PATH = get_path()
    e = Engine()
    # e.start(Anjuke, 'cd', 'zu', max_price=1300, contract_type=1, other='l2')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        e.async_start(Anjuke,
                      'cd',
                      'zu',
                      max_price=2000,
                      contract_type=1,
                      other='l2'))
    loop.close()
