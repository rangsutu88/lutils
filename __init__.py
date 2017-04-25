# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

import os
import re
import socket
import random
import bisect
import codecs
import urlparse
from bs4 import BeautifulSoup

LUTILS_ROOT = os.path.dirname(__file__)

def remove_tags(html):
    soup = BeautifulSoup(html)
    return ''.join(soup.findAll(text=True))

def weighted_choice(choices): #((value, per), (value, per), (value, per))
    values, weights = zip(*choices)
    total = 0
    cum_weights = []
    for w in weights:
        total += w
        cum_weights.append(total)
    x = random.random() * total
    i = bisect.bisect(cum_weights, x)
    return values[i]

def todir(content):
    content = ' '.join([c.strip() for c in content.splitlines()])
    for c in u'''/\\:*?"<>|#$[]+&^%@!~()'{},.−''':
        content = content.replace(c, '')
    return content.strip().replace('  ', '-').replace(' ', '-').replace(' ', '-').replace('--', '-').replace('--', '-').replace('--', '-')

def todir2(content):
    content = ' '.join([c.strip() for c in content.splitlines()])
    for c in u'''/\\:*?"<>|#$[]+&^%@!~()'{},.−''':
        content = content.replace(c, ' ')
    return content.strip().replace('  ', '-').replace(' ', '-').replace(' ', '-').replace('--', '-').replace('--', '-').replace('--', '-')

def todir3(content):
    content = ' '.join([c.strip() for c in content.splitlines()])
    for c in u'''/\\:*?"<>|#$[]+&^%@!~()'{},.−''':
        content = content.replace(c, ' ')
    return content.strip().replace('  ', ' ')

def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def pick_next_random_line(file, offset):
    while 1:
        try:
            file.seek(offset)
            chunk = file.read(CHUNK_SIZE)
            break
        except UnicodeDecodeError:
            offset += 10

    lines = chunk.splitlines()
    lines = lines[1:-1]
    line_offset = offset + len('\n') + chunk.find('\n')
    if len(lines) > 0:
        return line_offset, random.choice(lines)
    else:
        return line_offset, ''

CHUNK_SIZE = 10240
def read_random_lines(path, amount=5):

    results = []
    if isinstance(path, basestring) and os.path.exists(path):
        _length = os.stat(path).st_size
        if _length > 0:
#            with open(path) as input:
            with codecs.open(path, 'r', 'utf-8') as input:
                for x in range(amount):
                    _count = 10
                    while _count:
                        try:
                            _offset = _length - CHUNK_SIZE
                            if _offset > 0:
                                offset, line = pick_next_random_line(input, random.randint(0, _offset))
                            else:
                                offset, line = pick_next_random_line(input, 0)

                            v = line.strip()
                            if v:
                                results.append(v)
                                break
                        finally:
                            _count -= 1
    return results


def get_tld(url):

    url = "http://www.python.org"
    domain = urlparse.urlsplit(url)[1].split(':')[0]
    print "The domain name of the url is: ", domain


def _clean(html, remove=['br', 'hr']):
    html = re.compile('<!--.*?-->', re.DOTALL).sub('', html)  # remove comments
    if remove:
        # XXX combine tag list into single regex, if can match same at start and end
        for tag in remove:
            html = re.compile('<' + tag + '[^>]*?/>', re.DOTALL | re.IGNORECASE).sub('', html)
            html = re.compile('<' + tag + '[^>]*?>.*?</' + tag + '>', re.DOTALL | re.IGNORECASE).sub('', html)
            html = re.compile('<' + tag + '[^>]*?>', re.DOTALL | re.IGNORECASE).sub('', html)
    return html

def free_port():
    free_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    free_socket.bind(('0.0.0.0', 0))
    free_socket.listen(5)
    port = free_socket.getsockname()[1]
    free_socket.close()
    return port