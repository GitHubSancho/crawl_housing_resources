#!/usr/bin/env python
#-*- coding: utf-8 -*-
#FILE: main.py
#CREATE_TIME: 2022-09-07
#AUTHOR: Sancho
"""
爬取互联网上的住房信息
"""

import sys
import pandas as pd
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
        if not isinstance(args, tuple) and hasattr(args, '__call__'):
            self.fun = args
            instance: ResourcesBase = self.fun()
        elif hasattr(args[0], '__call__'):
            self.fun = args[0]
            instance: ResourcesBase = self.fun(*args[1:], **kwargs)
        else:
            raise f"请正确输入房源类：{args}"
        # f = resources_manager.Filter(self.fun)
        # resp = h.get_resources()
        # f.filter_html(*resp)
        downloader = Download(OBJECT_PATH)
        url = instance.build_url()
        params = instance.build_params()
        status, html, url, redirected_url = downloader.download_url(
            url, params)
        df, next_url = instance.filter_html(html)
        print(df)
        print(next_url)


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
    e.start(Anjuke, 'cd', 'zu', max_price=1000, contract_type=1, other='l2')
