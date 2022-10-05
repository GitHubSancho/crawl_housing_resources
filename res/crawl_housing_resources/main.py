#!/usr/bin/env python
#-*- coding: utf-8 -*-
#FILE: main.py
#CREATE_TIME: 2022-09-07
#AUTHOR: Sancho
"""
爬取互联网上的住房信息
"""
import os
from flask import Flask, redirect, render_template, request, url_for
import pandas as pd
import yaml
import sys
from time import sleep
from urllib.parse import urlparse
import requests
import webbrowser
import aiohttp
import asyncio
# ----
from resources_manager import ResourcesBase, Anjuke
from downloader import Download

# pandas输出设置项
pd.set_option('display.unicode.ambiguous_as_wide', True)  #处理数据的列标题与数据无法对齐的情况
pd.set_option('display.unicode.east_asian_width', True)  #无法对齐主要是因为列标题是中文


def load_cities() -> dict:
    "读取城市列表"
    with open('cities.yml', 'r', encoding='utf-8') as f:
        cities = yaml.load(f, Loader=yaml.CLoader)
    return cities


class Engine:
    def __init__(self) -> None:
        pass

    async def async_start(self, *args, **kwargs):
        # 判断传参格式,实例化房源类
        self._instantiation_instance(*args, **kwargs)

        # 下载和解析页面
        self.downloader = Download()  # 初始化下载器
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
        name = 'data.csv'
        data.to_csv(name, index=False, encoding='utf_8_sig')
        webbrowser.open('http://127.0.0.1:5000/')


class Appcation:
    parameter = {}
    template_dir = os.path.abspath('./res/templates/')
    app = Flask(__name__, template_folder=template_dir)

    def __init__(self) -> None:
        pass

    @staticmethod
    @app.route('/')
    def index():
        "首页"
        return render_template('index.html')

    @staticmethod
    @app.route('/result', methods=["GET", "POST"])
    def result():
        "返回结果"
        if request.method != "POST":
            return 'Wrong access method'

        result = request.form
        if city := load_cities().get(result['city']):
            return redirect(
                url_for('get_resources',
                        city=city,
                        terms=result['terms'],
                        min_price=result['min_price'],
                        max_price=result['max_price'],
                        room_type=result['room_type']))
        return f"未找到城市：{result['city']}"

    @staticmethod
    @app.route('/resources/<city><terms><min_price><max_price><room_type>')
    def get_resources(city, terms, min_price, max_price, room_type):
        """传递参数，获取数据"""
        # 找到文件路径
        # global MY_PATH, OBJECT_PATH
        # MY_PATH, OBJECT_PATH = get_path()

        # 设置异步循环
        # e = Engine()
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(
        #     e.async_start(Anjuke,
        #                   'cd',
        #                   'zu',
        #                   max_price=800,
        #                   contract_type=1,
        #                   other='l2'))
        # loop.close()

        # 返回数据
        # return f"hello {city} <br> {terms} <br>{min_price} <br>{max_price} <br>{room_type}<br>"
        return f"{city}"

    def run(self):
        self.app.run(debug=True)


if __name__ == "__main__":
    a = Appcation()
    a.run()