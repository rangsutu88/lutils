# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

import os
import logging
import urlparse
import json
import traceback
import datetime
import tables
from tables import *
from ..lrequest import LRequest

logger = logging.getLogger('lutils')


class Stocks(IsDescription):
    id                  = StringCol(20, pos=1)
    opening_price       = Float32Col(pos=2)
    highest_price       = Float32Col(pos=3)
    closing_price       = Float32Col(pos=4)
    floor_price         = Float32Col(pos=5)
    trading_volume      = Int64Col(pos=6)
    transaction_amount  = Int64Col(pos=7)
    # details             = StringCol


class StockDetails(IsDescription):
    id                  = StringCol(20, pos=1) # stock code_date
    time                = StringCol(10, pos=2)
    price               = Float32Col(pos=3)
    price_change        = Float32Col(pos=4)
    volume              = Int64Col(pos=5)
    turnover            = Int64Col(pos=6)
    nature              = StringCol(20, pos=7)

class LStockData():

    start_url = 'http://money.finance.sina.com.cn/corp/go.php/vMS_MarketHistory/stockid/%s.phtml'
    url_format = 'http://money.finance.sina.com.cn/corp/go.php/vMS_MarketHistory/stockid/%s.phtml?year=%s&jidu=%s'

    def __init__(self): #, input, output, **kwargs):
        # threading.Thread.__init__(self)

        # self.input = input
        # self.output = output
        self.lr = LRequest()



    def search(self, id, start_year=2007):
        try:
            # f = os.path.join(SAVE_BASE_PATH, '%s.txt' % id)
            # stock_file = open(f, 'w')
            stock_datas = []
            url = self.start_url % id
            logger.info('Load Url: %s' % url)
            self.lr.load(url)

            _start_year = self.lr.xpaths('//select[@name="year"]/option')[-1].attrib['value'].strip()
            if _start_year < '2004':
                _start_year = '2004'
            _start_year = int(_start_year)
            if start_year < _start_year:
                start_year = _start_year

            for year in range(start_year, 2017):
                for jidu in range(1, 5):
                    try:
                        _url = self.url_format % (id, year, jidu)
                        logger.info('Load: %s: %s' % (id, _url))
                        self.lr.load(_url)

                        if self.lr.body.find('FundHoldSharesTable') > -1:
                            records = list(self.lr.xpaths('//table[@id="FundHoldSharesTable"]/tr')[1:])
                            records.reverse()

                            for record in records:
                                _date = record.xpath('./td[1]/div')[0].text.strip()

                                detail_url = ''
                                if not _date:
                                    _date = record.xpath('./td[1]/div/a')[0].text.strip()
                                    detail_url = record.xpath('./td[1]/div/a')[0].attrib['href'].strip()

                                _opening_price = record.xpath('./td[2]/div')[0].text.strip()
                                _highest_price = record.xpath('./td[3]/div')[0].text.strip()
                                _closing_price = record.xpath('./td[4]/div')[0].text.strip()
                                _floor_price = record.xpath('./td[5]/div')[0].text.strip()
                                _trading_volume = record.xpath('./td[6]/div')[0].text.strip()
                                _transaction_amount = record.xpath('./td[7]/div')[0].text.strip()


                                _id = '%s_%s' % (id, _date)

                                details = []
                                if detail_url:

                                    params = urlparse.parse_qs(urlparse.urlparse(detail_url).query, True)
                                    detail_down_url = 'http://market.finance.sina.com.cn/downxls.php?date=%s&symbol=%s' % (params['date'][0], params['symbol'][0])
                                    self.lr.load(detail_down_url)
                                    logger.info('Load Detail: %s: %s' % (id, detail_down_url))

                                    if self.lr.body.find('language="javascript"') < 0:
                                        for line in self.lr.body.decode('gbk').splitlines()[1:]:
                                            nature = ''
                                            try:
                                                t, price, _price_change, volume, turnover, _nature = line.strip().split('	')
                                            except :
                                                logger.info(line)
                                                raise
                                            if _nature == u'卖盘':
                                                nature = 'sell'
                                            elif _nature == u'买盘':
                                                nature = 'buy'
                                            elif _nature == u'中性盘':
                                                nature = 'neutral_plate'
                                            else:
                                                nature = _nature

                                            price_change = '0.0'
                                            if _price_change != '--':
                                                price_change = _price_change


                                            details.append({'time': t,
                                                            'price': price,
                                                            'price_change': price_change,
                                                            'volume': volume,
                                                            'turnover': turnover,
                                                            'nature': nature,})


                                # self.stocks.put(_id, {'stock:opening_price': _opening_price,
                                #                       'stock:highest_price': _highest_price,
                                #                       'stock:closing_price': _closing_price,
                                #                       'stock:floor_price': _floor_price,
                                #                       'stock:trading_volume': _trading_volume,
                                #                       'stock:transaction_amount': _transaction_amount,
                                #                       'stock:details': json.dumps(details)})

                                # stock_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (_id, _opening_price, _highest_price, _closing_price, _floor_price, _trading_volume, _transaction_amount, json.dumps(details)))

                                stock_datas.append((_id, _opening_price, _highest_price, _closing_price, _floor_price, _trading_volume, _transaction_amount, details))
                    except :
                        raise

            # stock_file.close()
            return stock_datas
        except :
            raise


    def search_to_h5(self, code, save_path, start_year=2007):

        stock_datas = self.search(code, start_year)

        h5file = tables.open_file(save_path, 'w')
        try:

            stocks_group = h5file.create_group("/", 'stock', 'Stock Information')
            stock_table = h5file.create_table(stocks_group, 'stocks', Stocks, "Stock Table")
            stock = stock_table.row

            detail_table = h5file.create_table(stocks_group, 'details', StockDetails, "Stock Detail Table")
            detail = detail_table.row

            url = self.start_url % id
            logger.info('Load Url: %s' % url)
            self.lr.load(url)

            _start_year = self.lr.xpaths('//select[@name="year"]/option')[-1].attrib['value'].strip()
            if _start_year < '2004':
                _start_year = '2004'
            _start_year = int(_start_year)
            if start_year < _start_year:
                start_year = _start_year

            for year in range(start_year, 2017):
                for jidu in range(1, 5):
                    try:
                        _url = self.url_format % (id, year, jidu)
                        logger.info('Load: %s: %s' % (id, _url))
                        self.lr.load(_url)

                        if self.lr.body.find('FundHoldSharesTable') > -1:
                            records = list(self.lr.xpaths('//table[@id="FundHoldSharesTable"]/tr')[1:])
                            records.reverse()

                            for record in records:
                                _date = record.xpath('./td[1]/div')[0].text.strip()

                                detail_url = ''
                                if not _date:
                                    _date = record.xpath('./td[1]/div/a')[0].text.strip()
                                    detail_url = record.xpath('./td[1]/div/a')[0].attrib['href'].strip()

                                _opening_price = record.xpath('./td[2]/div')[0].text.strip()
                                _highest_price = record.xpath('./td[3]/div')[0].text.strip()
                                _closing_price = record.xpath('./td[4]/div')[0].text.strip()
                                _floor_price = record.xpath('./td[5]/div')[0].text.strip()
                                _trading_volume = record.xpath('./td[6]/div')[0].text.strip()
                                _transaction_amount = record.xpath('./td[7]/div')[0].text.strip()

                                _id = '%s_%s' % (id, _date)

                                details = []
                                if detail_url:

                                    params = urlparse.parse_qs(urlparse.urlparse(detail_url).query, True)
                                    detail_down_url = 'http://market.finance.sina.com.cn/downxls.php?date=%s&symbol=%s' % (
                                    params['date'][0], params['symbol'][0])
                                    self.lr.load(detail_down_url)
                                    logger.info('Load Detail: %s: %s' % (id, detail_down_url))

                                    if self.lr.body.find('language="javascript"') < 0:
                                        for line in self.lr.body.decode('gbk').splitlines()[1:]:
                                            nature = ''
                                            try:
                                                t, price, _price_change, volume, turnover, _nature = line.strip().split('	')
                                            except:
                                                logger.info(line)
                                                raise
                                            if _nature == u'卖盘':
                                                nature = 'sell'
                                            elif _nature == u'买盘':
                                                nature = 'buy'
                                            elif _nature == u'中性盘':
                                                nature = 'neutral_plate'
                                            else:
                                                nature = _nature

                                            price_change = '0.0'
                                            if _price_change != '--':
                                                price_change = _price_change

                                            details.append({'time': t,
                                                            'price': price,
                                                            'price_change': price_change,
                                                            'volume': volume,
                                                            'turnover': turnover,
                                                            'nature': nature, })


                                details.reverse()
                                for d in details:
                                    detail['id'] = _id

                                    detail['time'] = d['time']
                                    detail['price'] = d['price'].split(u'\u0000', 1)[0] if d['price'] else 0.0
                                    detail['price_change'] = d['price_change']
                                    detail['volume'] = d['volume']
                                    detail['turnover'] = d['turnover']
                                    detail['nature'] = d['nature']

                                    detail.append()


                                stock['id'] = _id
                                stock['opening_price'] = _opening_price
                                stock['highest_price'] = _highest_price
                                stock['closing_price'] = _closing_price
                                stock['floor_price'] = _floor_price
                                stock['trading_volume'] = _trading_volume
                                stock['transaction_amount'] = _transaction_amount

                                stock.append()
                    except:
                        raise

            stock_table.flush()
        except:
            # logger.error(traceback.format_exc())
            raise
        finally:
            h5file.close()

def get_all_codes():
    stock_code_url = 'http://quote.eastmoney.com/stocklist.html'
    exchanges = ['ss', 'sz', 'hk']

    lr = LRequest()
    stock_codes = []

    lr.load(stock_code_url)

    # stock_eles = lr.xpath('//div[@id="quotesearch"]//li/a[@target="_blank"]')
    stock_exchange_eles = lr.xpaths('//div[@id="quotesearch"]/ul')

    for i, stock_exchange_ele in enumerate(stock_exchange_eles):
        stock_eles = stock_exchange_ele.xpath('./li/a[@target="_blank"]')
        for stock_ele in stock_eles:
            # code = stock_ele.get('href').rsplit('/', 1)[-1].split('.', 1)[0]
            if stock_ele.text:
                code = stock_ele.text.split('(', 1)[-1].split(')', 1)[0]

                stock_codes.append((exchanges[i], code))

    return stock_codes


def get_new_stock_code(year=None):

    lr = LRequest()
    stock_codes = []

    if year is None:
        year = str(datetime.date.today().year)

    lr.load('http://quotes.money.163.com/data/ipo/shengou.html?reportdate=%s' % year)
    # lr.loads(BeautifulSoup(lr.body).prettify())

    for ele in lr.xpaths('//table[@id="plate_performance"]/tr/td[3]'):  # codes
        # print ele.text.strip()
        stock_codes.append(ele.text.strip())

    for ele in lr.xpaths('//div[@class="fn_cm_pages"]//a[contains(@href, "page")]')[:-1]:  # pages
        u = urlparse.urljoin('http://quotes.money.163.com/data/ipo/shengou.html', ele.attrib['href'])

        lr.load(u)
        lr.loads(BeautifulSoup(lr.body).prettify())

        for ce in lr.xpaths('//table[@id="plate_performance"]/tr/td[3]'):  # codes
            # print ce.text.strip()
            stock_codes.append(ce.text.strip())

    return stock_codes


if __name__ == '__main__':

    # for i in get_all_codes():
    #     print i

    # for i in get_new_stock_code():
    #     print i

    # lr = LRequest()
    # lr.load(stock_code_url)
    #
    # for a in lr.xpaths('//div[@id="quotesearch"]//li/a[@target="_blank"]'):
    #     print a.text

    id = '603858'
    start_year = 2007

    ls = LStock()
    # for data in ls.search(id, start_year):
    #     print data

    ls.search_to_h5(id, 'F:\\603858.h5', start_year)