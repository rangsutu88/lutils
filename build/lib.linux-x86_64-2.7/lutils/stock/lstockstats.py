# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

import logging
from stockstats import StockDataFrame
import functools

log = logging.getLogger('lutils')


def change_macd_name(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        result = func(*args, **kwargs)

        result.rename(columns={"macd": "diff", "macds": "dea", 'macdh': 'macd'}, inplace=True)
        return result

    return wrapped


class LStockDataFrame(StockDataFrame):

    # @staticmethod
    # def init_columns(obj, columns):
    #     if isinstance(columns, list):
    #         for column in columns:
    #             LStockDataFrame.__init_column(obj, column)
    #     else:
    #         LStockDataFrame.__init_column(obj, columns)
    #
    # @staticmethod
    # def __init_column(df, key):
    #     if key not in df:
    #         if len(df) == 0:
    #             df[key] = []
    #         else:
    #             LStockDataFrame.__init_not_exist_column(df, key)
    #
    # @classmethod
    # def __init_not_exist_column(cls, df, key):
    #
    #     super(LStockDataFrame, cls).__init_not_exist_column(df, key)
    #
    #     if key == 'macd':
    #         df.rename(columns={"macd": "diff", "macds": "dea", 'macdh': 'macd'}, inplace=True)

    @change_macd_name
    def __getitem__(self, item):
        result = super(LStockDataFrame, self).__getitem__(item)
        return result