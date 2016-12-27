# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

import StringIO, urllib2, time
from ClientForm import ParseFile
from lutils.lrequest import LRequest


gsa_form_str = '''<form method="post" enctype="multipart/form-data" action="http://%s:%s/gsa_test.gsa">
<input type="file" name="file" value="">
<input type="submit" value="Submit">
</form>'''

class GsaCaptcha():

    lr = None
    ip = ''
    port = ''

    def __init__(self, ip='127.0.0.1', port='80'):
        self.ip = ip
        self.port = port

        self.lr = LRequest()

    def decode(self, file_path):
        try:

            form = ParseFile(StringIO.StringIO(gsa_form_str % (self.ip, self.port)), base_uri='http://%s:%s' % (self.ip, self.port))[0]
            form.add_file(open(file_path, 'rb'), name='file')
            self.lr.load(form.click(), is_xpath=False)
            gsa_result = self.lr.body
            result = ''
            if gsa_result.find('<span id="captcha_result">') > -1:
                result = gsa_result.split('<span id="captcha_result">')[1].split('</span>')[0]

            return result
        except:
            raise

    def decode_stream(self, file_data):
        try:

            form = ParseFile(StringIO.StringIO(gsa_form_str % (self.ip, self.port)), base_uri='http://%s:%s' % (self.ip, self.port))[0]
            form.add_file(StringIO.StringIO(file_data), name='file')
            self.lr.load(form.click(), is_xpath=False)
            result = ''
            gsa_result = self.lr.body
            if gsa_result.find('<span id="captcha_result">') > -1:
                result = gsa_result.split('<span id="captcha_result">')[1].split('</span>')[0]

            return result
        except:
            raise

    def decode_url(self, url):
        try:
            self.lr.load(url)

            form = ParseFile(StringIO.StringIO(gsa_form_str % (self.ip, self.port)), base_uri='http://%s:%s' % (self.ip, self.port))[0]
            form.add_file(StringIO.StringIO(self.lr.body), name='file')
            self.lr.load(form.click(), is_xpath=False)
            result = ''
            gsa_result = self.lr.body
            if gsa_result.find('<span id="captcha_result">') > -1:
                result = gsa_result.split('<span id="captcha_result">')[1].split('</span>')[0]

            return result
        except:
            raise
