# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'


class LCache():

    def __init__(self, root, **kwargs):

        self.root = root

    def exists_cache(self, cache_name, reduce=False):
        cache_path = os.path.join(self.CACHE_ROOT, cache_name[0], cache_name[1], cache_name)
        return os.path.exists(cache_path)

    def load_cache(self, cache_name):
        cache_path = os.path.join(self.CACHE_ROOT, cache_name[0], cache_name[1], cache_name)
        # exists check

        try:
            return cPickle.loads(gzip.GzipFile(cache_path, 'rb').read())
        except:
            return {}

    def save_cache(self, cache_name, data, reduce=True):
        _p = os.path.join(self.CACHE_ROOT, cache_name[0], cache_name[1])
        if not os.path.exists(_p): os.makedirs(_p)

        cache_path = os.path.join(self.CACHE_ROOT, cache_name[0], cache_name[1], cache_name)

        gzip_file = gzip.open(cache_path, 'wb')
        gzip_file.write(cPickle.dumps(data))
        gzip_file.close()