import os
from flask import Flask, render_template, request
import pandas as pd
import yaml


def read_data():
    return pd.read_csv('data.csv', encoding='utf_8_sig')


# @app.route('/')
# def index():
#     df = read_data()
#     data = df.to_html(index=True)
#     return render_template('index.html', data=data)


def load_cities() -> dict:
    with open('cities.yml', 'r', encoding='utf-8') as f:
        cities = yaml.load(f, Loader=yaml.CLoader)
    return cities


class Appcation:
    parameter = {}
    template_dir = os.path.abspath('./res/templates/')
    app = Flask(__name__, template_folder=template_dir)

    def __init__(self) -> None:
        pass

    @staticmethod
    @app.route('/')
    def index():
        return render_template('index.html')

    @staticmethod
    @app.route('/result', methods=["GET", "POST"])
    def result():
        if request.method != "POST":
            return 'Wrong access method'

        result = request.form
        if city := not load_cities().get(result['city']):
            return f"未找到城市：{result['city']}"
        return f'success: {city}'
