from abc import ABCMeta, abstractmethod
from lxml import etree
from pandas import DataFrame


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