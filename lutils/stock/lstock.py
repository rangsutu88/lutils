from __future__ import division
# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'


import os
import gc
import numpy as np
import pandas as pd
import tables as tb
from stockstats import StockDataFrame
from lstockstats import LStockDataFrame

# pd.set_option('expand_frame_repr', False)

from decorators import *

class LStock():

    def __init__(self):
        pass


    # def clear_price_change(self, datas):
    #
    #     datas.loc[datas['price_change'] == datas['price'], 'price_change'] = 0.0
    #
    #     datas.loc[datas['price'] == 0.0, 'price_change'] = 0.0
    #
    #     details.loc[details['price'] == 0.0]


    @detail_price_change_equal_price
    @detail_price
    @detail_nature
    @detail_reindex
    def clear_detail(self, datas):
        return datas


    @stock_reindex
    def clear_stock(self, datas):
        return datas

    def get_stock(self, h5file):
        stock_datas = pd.read_hdf(h5file, '/stock/stocks')
        return StockDataFrame(self.clear_stock(datas=stock_datas))

    def get_detail(self, h5file):
        detail_datas = pd.read_hdf(h5file, '/stock/details')
        return self.clear_detail(datas=detail_datas)


    def ratio_day(self, stocks, details, day):
        if day in details.index:
            day_details = details.ix[day]
            # detail_change = (day_details['price_change'] * day_details['volume']).sum() > 0
            # day_change = (stocks[day, 'closing_price'] - stocks[day, 'opening_price']) > 0


            # return (stocks.ix[day, 'closing_price'] - stocks.ix[day, 'opening_price']), (day_details['price_change'] * day_details['volume']).sum()

            return (stocks.ix[day, 'closing_price'] - stocks.ix[day, 'opening_price']), (day_details[day_details['nature'] != 0]['price_change'] * day_details[day_details['nature'] != 0]['volume']).sum()

        else:

            return (stocks.ix[day, 'closing_price'] - stocks.ix[day, 'opening_price']), 0




lstock = LStock()


if __name__ == '__main__':

    path = 'K:\\\stock_data'
    # for f in os.listdir(path):
    #
    #     h5path = os.path.join(path, f)
    #     # details = pd.read_hdf(h5path, '/stock/details')
    #     details = stock.get_detail(h5path)
    #
    #     if details[np.abs(details['price_change']) >= 5].size > 0:
    #         print f
    #
    #     gc.collect()

    # h5path = os.path.join('K:\\\stock_data\\002130.h5')
    # details = pd.read_hdf(h5path, '/stock/details')
    #
    # index1 = details[details['price_change'] == details['price']].index[0]
    # index2 = details[(details['price'] == 0.0) & (details['volume'] == 0)].index[0]
    # print index1, index2
    #
    # print details.ix[index1]
    # print '***'
    # print details.ix[index2]
    # data2 = stock.clear_detail(datas=details)
    # print '####################################'
    # print data2.ix[index1]
    # print '***'
    # print data2.ix[index2]
    #
    # print '####################################'
    # print data2[:5]

    # h5path = 'K:\\\stock_data\\002107.h5'
    #
    # details = stock.get_detail(h5path)


    ###################################################
    # h5file = os.path.join(path, '002139.h5')
    # stocks = stock.get_stock(h5file)
    # details = stock.get_detail(h5file)
    #
    # stocks.to_hdf('K:\\002139.h5','/stock/stocks',append=True)
    # details.to_hdf('K:\\002139.h5','/stock/details',append=True)

    # for f in os.listdir(path):
    #     h5file = os.path.join(path, f)
    #
    #     stocks = stock.get_stock(h5file)
    #     details = stock.get_detail(h5file)
    #
    #     c = 0
    #     r = 0
    #     for i in stocks.index:
    #         a, b = stock.ratio_day(stocks, details, i)
    #         if (a > 0) == (b > 0):
    #             r += 1
    #
    #         c += 1
    #
    #     print f, r, c, r/c
    #
    #     gc.collect()

    #################
    # h5path = 'K:\\\stock_data\\002139.h5'
    # stocks = stock.get_stock(h5path)
    # details = stock.get_detail(h5path)
    #
    # c = 0
    # r = 0
    # for i in stocks.index[50:]:
    #     a, b = stock.ratio_day(stocks, details, i)
    #
    #     if (a > 0) == (b > 0):
    #         r += 1
    #     else:
    #         print i
    #
    #     c += 1
    #
    # print f, r, c, r/c

    f = 'K:\\stock_data\\002142.h5'
    details = stock.get_detail(f)
