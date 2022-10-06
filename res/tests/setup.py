#!/usr/bin/env python
#-*- coding: utf-8 -*-
#FILE: main.py
#CREATE_TIME: 2022-09-07
#AUTHOR: Sancho
"""
爬取互联网上的住房信息
"""
from os import path as ospath
from flask import Flask, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
import pandas as pd
from pandas import DataFrame, concat
from yaml import load, CLoader
from time import sleep
from urllib.parse import urlparse
from webbrowser import open as wopen
import asyncio
from aiohttp import ClientSession
from random import choice
from sys import platform, path as syspath, argv as sysargv
from abc import ABCMeta, abstractmethod
from lxml import etree
# ----

# pandas输出设置项
pd.set_option('display.unicode.ambiguous_as_wide', True)  #处理数据的列标题与数据无法对齐的情况
pd.set_option('display.unicode.east_asian_width', True)  #无法对齐主要是因为列标题是中文


class ResourcesBase(metaclass=ABCMeta):
    # 房源基类
    # C = ['cd']
    # T = ['zu']

    def __init__(self, city, terms) -> None:

        # if city not in self.C:
        #     raise f"{ValueError}\n请输入列表中的城市：{self.C}"
        # if terms not in self.T:
        #     raise f"{ValueError}\n请输入列表中的合同方式：{self.T}"
        self.city = city
        self.terms = terms

    @abstractmethod
    def build_url():
        pass

    @abstractmethod
    def build_params():
        pass

    @abstractmethod
    def filter_html():
        pass


class Anjuke(ResourcesBase):
    # 安居客
    def __init__(self,
                 city: str,
                 terms: str,
                 min_price: int = None,
                 max_price: int = None,
                 room_type: int = None,
                 contract_type: int = None,
                 other: str = None) -> None:
        """
        city:（必选）城市的拼音简写，如成都：`cd`
        terms:（必选）合同类型拼音，如租房：`zu`
        min_price:可选最低价格
        max_price:可选最高价格
        room_type:可选几房室，1~5
        contract_type:可选`1`整租，`2`合租
        other:`qhy1`实拍房源,`l1`真实房源，`l2`个人房源
        """
        # 初始化
        super().__init__(city, terms)
        self.min_price = min_price
        self.max_price = max_price
        self.room_type = room_type
        self.contract_type = contract_type
        self.other = other

    def build_url(self) -> str:
        # 拼接地址
        self.url = f"https://{self.city}.{self.terms}.anjuke.com/fangyuan/"
        # 检查访问选项拼接到地址
        url = ''
        if self.room_type:
            url = f'fx{self.room_type}'
        if url and self.contract_type:
            url = f'{url}-x{self.contract_type}'
        elif self.contract_type:
            url = f'x{self.contract_type}'
        if url and self.other:
            url = f'{url}-{self.other}'
        elif self.other:
            url = self.other
        return self.url + url

    def build_params(self) -> str:
        # 参数设置
        return {
            "from": "HomePage_TopBar",
            "from_price": self.min_price or '',
            "to_price": self.max_price or ''
        }

    def filter_html(self, html):
        # 过滤网页
        df = DataFrame(
            [], columns=['title', 'details', 'address', 'tags', 'price'])
        html = etree.HTML(html)
        aa = html.xpath('//*[@class="zu-itemmod"]')
        next_urls = html.xpath('//*[@class="multi-page"]/a/@href')
        next_urls = list(set(next_urls))  # 去重

        for a in aa:
            title = a.xpath('./div[1]/h3/a/b/text()')[0]
            details = a.xpath('string(./div[1]/p[1])').strip()
            addresses = a.xpath('string(./div[1]/address[1])').strip().replace(
                " ", "").replace("\n", "|")
            tags = a.xpath('string(./div[1]/p[2])').strip().replace(
                " ", "").replace("\n", "|")
            price = a.xpath('string(./div[2]/p[1])')
            df.loc[len(df)] = [title, details, addresses, tags, price]

        # 返回解析的数据和下一页的链接
        return df, next_urls


class Download:
    @staticmethod
    def filter_url(url):
        # 去除链接多余参数
        if not url:
            return False
        url = urlparse(url)
        return f'{url.scheme}://{url.netloc}{url.path}'

    def __init__(self) -> None:
        _, self.object_path = get_path()
        self.ua_list = self._get_ua_list()
        self.data = DataFrame()

    def _get_ua_list(self):
        path = "ua.yml"
        with open(path, 'r', encoding='utf-8') as f:
            ua_list = load(f, Loader=CLoader)
        return ua_list

    async def async_download_url(self, url, params=None, headers=None):
        headers = headers or choice(self.ua_list)
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
            self.data = concat([self.data, df])  # 合并数据

            # 增加新链接
            for new_url in next_urls:
                new_url = self.filter_url(new_url)  # 格式化链接
                if new_url in url_pool:  # 去重
                    continue
                url_pool[new_url] = 1  # 标记新链接
            url_pool[url] = 0  # 标记已下载链接
        return url_pool

    async def async_fetch(self, html_filter, url_pool: dict, params):
        async with ClientSession() as self.session:
            count = 0
            while any(url_pool.values()):
                resp = await self._async_get_resp(url_pool, params)  # 下载并返回网页
                url_pool = self._parse_resp(html_filter, url_pool,
                                            resp)  # 解析网页

                count += len(resp)
                print(f"已下载第{count}页")
                await asyncio.sleep(6)  # 延迟访问，太快会触发访问限制，需要手动进网页输入验证
        return self.data


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
        data = await self._async_get_data()  # 解析网页数据

        # 保存结果
        data.to_csv('data.csv', index=False, encoding='utf_8_sig')

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


class Register(FlaskForm):
    username = StringField(
        lable='city',
        validators=[DataRequired()],  # 验证是否为空
        render_kw={  # 额外属性
            'placeholder': 'city',
            'class': 'input_text'
        })


class Appcation:
    parameter = {}
    app = Flask(__name__)

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
        cities = load_cities()
        if city := cities.get(result.get('city', type=str)):
            return redirect(
                url_for('get_resources',
                        city=city,
                        terms=result.get('terms', type=str),
                        min_price=result.get('min_price', type=str),
                        max_price=result.get('max_price', type=str),
                        room_type=result.get('room_type', type=str)))
        return f"未找到城市：{result.get('city')}"

    @staticmethod
    @app.route('/resources/>')
    def get_resources():
        """传递参数，获取数据"""
        # 取发送值
        data = request.values
        _data = {
            "city": data.get('city'),
            "terms": data.get('terms'),
            "min_price": data.get('min_price'),
            "max_price": data.get('max_price'),
            "room_type": data.get('room_type')
        }

        # 执行任务
        run_engine(_data)
        data = load_data().to_html(index=True)
        return render_template('resources.html', data=data)

    def run(self):
        wopen('http://127.0.0.1:5000/')
        self.app.run()


def get_path():
    # 根据操作系统找到当前文件路径
    if platform == "win32":
        p = '\\'
    else:
        p = '/'
    my_path = syspath[0]
    object_path = f'{my_path}{p}..{p}..{p}'
    return my_path, object_path


def load_data():
    return pd.read_csv('data.csv', encoding='utf_8_sig')


def load_cities() -> dict:
    "读取城市列表"
    with open('cities.yml', 'r', encoding='utf-8') as f:
        cities = load(f, Loader=CLoader)
    return cities


def run_engine(data):
    # 设置异步循环
    fun = Anjuke  # 首先，安居客吧
    e = Engine()
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        e.async_start(
            fun,
            data['city'],
            data['terms'],
            data['min_price'],
            data['max_price'],
        ))
    loop.close()


if __name__ == "__main__":
    print(__file__)
    a = Appcation()
    a.run()