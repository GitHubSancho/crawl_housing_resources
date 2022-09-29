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

    async def async_start(self, *args, **kwargs):
        # 判断传参格式,实例化房源类
        self._instantiation_instance(*args, **kwargs)

        # 下载和解析页面
        self.downloader = Download(OBJECT_PATH)  # 初始化下载器
        self.url = self.instance.build_url()  # 在房源类中格式化url
        self.params = self.instance.build_params()  # 在房源类中格式化参数
        data = await self._async_get_data()

        # 显示结果
        self._open_app(data)

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

    async def _async_get_data(self):
        self.url_pool = {self.url: 1}
        return await self.downloader.async_fetch(self.instance.filter_html,
                                           self.url_pool, self.params)

    def _open_app(self, data: pd.DataFrame):
        # 应用flask
        name = 'data.csv'
        data.to_csv(name, index=False, encoding='utf_8_sig')
        webbrowser.open('http://127.0.0.1:5000/')
        app.run()


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
