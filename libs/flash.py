import requests
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class FlashClient:

    def __init__(self, url):
        self.url = url

    def init(self, **kwargs):
        return self._post(path='/init', **kwargs)

    def multisignature(self, **kwargs):
        return self._post(path='/multisignature', **kwargs)

    def settlement(self, **kwargs):
        return self._post(path='/settlement', **kwargs)

    def transfer(self, **kwargs):
        return self._post(path='/transfer', **kwargs)

    def sign(self, **kwargs):
        return self._post(path='/sign', **kwargs)

    def apply(self, **kwargs):
        return self._post(path='/apply', **kwargs)

    def close(self, **kwargs):
        return self._post(path='/close', **kwargs)

    def fund(self, **kwargs):
        return self._post(path='/fund', **kwargs)

    def finalize(self, **kwargs):
        return self._post(path='/finalize', **kwargs)

    def _post(self, path, **kwargs):
        response = requests.post(self.url + path, json=kwargs)
        if response.status_code >= 400:
            logger.info(response.text)
        response.raise_for_status()
        return response.json()
