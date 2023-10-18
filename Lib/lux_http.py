import os
import requests
from urllib import request


class Requests:

    @staticmethod
    def get(url):
        data = None
        try:
            response = requests.get(url)
            data = response.json()
        except Exception as e:
            pass

        return data


class RequestFile:

    def __init__(self, logger):
        self.logger = logger

    def wget(self, url, path=os.path.dirname(__file__)):

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
