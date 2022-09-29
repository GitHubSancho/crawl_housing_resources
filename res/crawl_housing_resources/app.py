from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)


def read_data():
    return pd.read_csv('data.csv', encoding='utf_8_sig')


@app.route('/')
def index():
    df = read_data()
    data = df.to_html(index=True)
    return render_template('index.html', data=data)
