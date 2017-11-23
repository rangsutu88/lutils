# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

import urllib, re
from bs4 import BeautifulSoup
from urllib2 import HTTPErrorProcessor
from lutils.lrequest import LRequest

class GoogleHTTPErrorProcessor(HTTPErrorProcessor):

    handler_order = 1000

    def http_response(self, request, response):
        code, msg, hdrs = response.code, response.msg, response.info()

        if not (200 <= code < 300 or code == 503):
            response = self.parent.error(
                'http', request, response, code, msg, hdrs)

        return response

    https_response = http_response


class GoogleSearch(object):

    search_url = 'https://www.google.%(tld)s/search?q=%(query)s&hl=%(lang)s&filter=%(filter)d&num=%(num)d&start=%(start)s&btnG=Google+Search'

    def __init__(self, query, *args, **kwargs):

        self.query = query

        self._tld = kwargs.get('tld', 'com')
        self._filter = kwargs.get('filter', 0)
        self._lang = kwargs.get('lang', 'en')
        self._num = kwargs.get('num', 100)
        self._page = kwargs.get('page', 0)

        timeout = kwargs.get('timeout', 90)
        string_proxy = kwargs.get('string_proxy', None)

        self.lr = LRequest(timeout=timeout, string_proxy=string_proxy, handers=[GoogleHTTPErrorProcessor(), ])


    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, value):
        self._page = value


    def _get_result(self):
        safe_url = self.search_url % {'query': urllib.quote_plus(self.query),
                            'start': self.page * self._num,
                            'num': self._num,
                            'tld' : self._tld,
                            'lang' : self._lang,
                            'filter': self._filter}

        print safe_url
        self.lr.load(safe_url)

        results = []
        i = 0
        for r in self.lr.xpath('//li[@class="g"]'):
            i += 1
            result = {}
            result['title'] = ''.join(r.xpath('./div/h3//text()'))
            result['description'] = ''.join(r.xpath('./div//span[@class="st"]//text()'))
            result['url'] = ''.join(r.xpath('./div/h3/a/@href'))

            results.append(result)

        print i

        return results

    def get_result(self):

        return self._get_result()



if __name__ == '__main__':

    g = GoogleSearch('inurl:guestbook site:.com 1..10', string_proxy='socks5://192.168.1.195:1075')


    results = g.get_result()
    for r in results:
        print r

#    print results

    open('D:\\code\\python\\xxx.html', 'w').write(g.lr.body)


#    from lxml import html
#
#    root = html.fromstring(open('D:\\code\\python\\xxx.html').read())
#
#    for r in root.xpath('//li[@class="g"]'):
#        result = {}
#        result['title'] = ''.join(r.xpath('./div/h3//text()'))
#        result['description'] = ''.join(r.xpath('./div//span[@class="st"]//text()'))
#        result['url'] = ''.join(r.xpath('./div/h3/a/@href'))
#
#        print result


