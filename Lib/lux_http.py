import os
import requests
from urllib import request, error
import sys
import shutil


class Requests:

    @staticmethod
    def get(url):
        response = requests.get(url)
        return response.json()


class RequestFile:

    def __init__(self, logger):
        self.logger = logger

    def wget(self, url, path="."):

        def _progress(block_num, block_size, total_size):
            pass

        ret = 0
        filename = url.split('/')[-1]
        try:
            filepath, _ = request.urlretrieve(url, os.path.join(path, filename), _progress)
            self.logger.info(f">> Download {filename} complete")
        except Exception as e:
            ret = -1
        return ret

    def remove_file_by_name(self, name, path="."):
        abs_name = os.path.join(path, name)
        if os.path.isfile(abs_name):
            os.remove(abs_name)
