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
# ----
from resources_manager import ResourcesBase, Anjuke
from downloader import Download

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
        name = '租房收集.csv'
        data.to_csv(name, index=False,encoding='utf_8_sig')
        print(f"已保存: 请在{name}中查看")

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
            sleep(5)
        return data


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
    e.start(Anjuke, 'cd', 'zu', max_price=1500, contract_type=1, other='l2')
