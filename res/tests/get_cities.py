import requests
import cchardet
from lxml import etree
import re
import yaml

url = 'https://www.anjuke.com/sy-city.html'
_xpath = '//*[@class="ajk-city-cell-content"]/li/a'

resp = requests.get(url)
encoding = cchardet.detect(resp.content)['encoding']
resp.encoding = encoding
html = etree.HTML(resp.text)

cities = list(html.xpath(f'{_xpath}/text()'))
cities = [str(city) for city in cities]
links = list(html.xpath(f'{_xpath}/@href'))
links = [
    re.findall(r'(?:^http.*?//)(.*?)(?:.anjuke.com)', _str)[-1]
    for _str in links
]

cities_dict = dict(zip(cities, links))
with open('cities.yml', mode='w', encoding='utf-8') as f:
    yaml.dump(cities_dict, f, Dumper=yaml.SafeDumper,allow_unicode=True)

print(cities_dict)