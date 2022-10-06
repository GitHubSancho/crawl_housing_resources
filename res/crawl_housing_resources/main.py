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
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length
import pandas as pd
from yaml import load, CLoader
from time import sleep
from urllib.parse import urlparse
from webbrowser import open as wopen
import asyncio
# ----
from resources_manager import ResourcesBase, Anjuke
from downloader import Download

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
    template_dir = ospath.abspath('./res/templates/')
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
    a = Appcation()
    a.run()