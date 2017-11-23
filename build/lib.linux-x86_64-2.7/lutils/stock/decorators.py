# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

import gc
import time
import functools
import numpy as np
import pandas as pd

def detail_price_change_equal_price(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        datas = kwargs.get('datas')

        datas.loc[datas['price_change'] == datas['price'], 'price_change'] = 0.0

        kwargs.setdefault('datas', datas)
        return func(*args, **kwargs)

    return wrapped


def detail_price(func):

    @functools.wraps(func)
    def wrapped(*args, **kwargs):

        datas = kwargs.get('datas')

        # indexs = datas[(datas['price'] == 0.0) & (datas['volume'] == 0)].index
        # datas.loc[indexs,'price'] = np.abs(datas.ix[indexs,'price_change'])
        # datas.loc[indexs,'price_change'] = 0.0

        indexs = datas[(datas['price'] < np.abs(datas['price_change'])) & (datas['volume'] == 0)].index
        datas.loc[indexs,'price'] = np.abs(datas.ix[indexs,'price']) + np.abs(datas.ix[indexs,'price_change'])
        datas.loc[indexs,'price_change'] = 0.0


        kwargs.setdefault('datas', datas)
        return func(*args, **kwargs)

    return wrapped


def detail_nature(func):

    @functools.wraps(func)
    def wrapped(*args, **kwargs):

        datas = kwargs.get('datas')

        datas.loc[datas['nature'] == 'buy', 'nature'] = 1
        datas.loc[datas['nature'] == 'sell', 'nature'] = -1
        datas.loc[datas['nature'] == 'neutral_plate', 'nature'] = 0

        # datas['nature'].apply(pd.to_numeric)
        datas.ix[:, 'nature'] = datas.ix[:, 'nature'].astype('int8')

        kwargs.setdefault('datas', datas)
        return func(*args, **kwargs)

    return wrapped


def detail_reindex(func):

    @functools.wraps(func)
    def wrapped(*args, **kwargs):

        datas = func(*args, **kwargs)

        # datas.loc[:,'id'] = datas['id'].str.split('_', 1, expand=True).ix[:,1]
        # _datas = datas.set_index([datas['id'], datas['time']])
        # _datas.drop(['id', 'time'], axis=1, inplace=True)

        # gc.collect()
        # return _datas

        _datas = datas.set_index(datas['date'])
        gc.collect()
        return _datas

    return wrapped


def stock_reindex(func):

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        datas = func(*args, **kwargs)

        # datas.loc[:,'id'] = datas['id'].str.split('_', 1, expand=True).ix[:,1]
        # _datas = datas.set_index(datas['id'])
        # _datas.drop('id', axis=1, inplace=True)

        # gc.collect()
        # return _datas

        _datas = datas.set_index(datas['date'])

        gc.collect()
        return _datas

    return wrapped
