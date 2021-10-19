import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
import logging
import json

class Bacon_Package(object):
    """
    Bacon
    =======
    A set of function wich handle data returned by service 'Bacon in json' 
    http://documentation.abes.fr/aidebacon/index.html#WebservicePackage
    On init take a package identifierin argument
    ex : https://bacon.abes.fr/package2kbart/CAIRN_COUPERIN_PSYCHOLOGIE.json
"""

    def __init__(self,pk_id,service='bacon'):
        self.logger = logging.getLogger(service)
        self.endpoint = "https://bacon.abes.fr/package2kbart/"
        self.service = service
        self.pk_id = pk_id
        #20190905 retry request 3 time s in case of requests.exceptions.ConnectionError
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        response = session.request(
            method='GET',
            headers= {
                "User-Agent": "{}".format(service),
                "Accept": "'application/json'"
        },
            url= '{}/{}.json'.format(self.endpoint, self.pk_id),)
        try:
            response.raise_for_status()  
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.exceptions.RequestException) :
            self.logger.warning("Alma_Apis :: HTTP Status: {} || Method: {} || URL: {} || Response: {}".format(response.status_code,response.request.method, response.url, response.text))
            self.status = "Error"
            self.error_descr = "{} -- {}".format(response.status_code, response.url)
        self.kbart =  response.json()
        # self.logger.debug(response.json())
        self.list_online_id = self.get_list_online_id()
        self.logger.debug(self.list_online_id)

    def get_list_online_id(self):
        list_index_by_id = []
        for title in self.kbart['query']['kbart'] :
            if title['online_identifier'] :
                my_dict = {title['online_identifier'] : title }
                list_index_by_id.append(my_dict)
                self.logger.debug(title['online_identifier'])
        return list_index_by_id   