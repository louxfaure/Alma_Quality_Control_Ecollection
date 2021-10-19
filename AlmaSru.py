import os
# external imports
import requests
import xml.etree.ElementTree as ET
import logging
import urllib.parse
import Isbns
# internal import




ns = {'sru': 'http://www.loc.gov/zing/srw/',
        'marc': 'http://www.loc.gov/MARC21/slim' }


class AlmaSru(object):

    def __init__(self, query, index, operator = '=' ,noticesSuppr=False,complex_query=False,institution ='network',service='AlmaSru',instance='Prod'):
        self.logger = logging.getLogger(service)
        self.institution = institution
        self.service = service
        self.instance = instance
        self.query = query
        self.index = index
        self.operator = operator
        self.noticesSuppr = noticesSuppr
        self.complex_query = complex_query
        self.result = self.sru_request()
        if self.status == True :
            nb_result = self.get_nombre_resultats()
            if  nb_result != '1' :
                self.status = False
                self.error_msg = "0 ou plusieus notices pour le même MMSID"
            else :
                self.status = True
                self.error_msg = ""
                self.record = self.result.find("sru:records/sru:record/sru:recordData/marc:record",ns)
    @property

    def baseurl(self):
        if self.instance == 'Test' :
            return "https://pudb-{}-psb.alma.exlibrisgroup.com/view/sru/{}?version=1.2&operation=searchRetrieve".format(self.institution.lower(),"33PUDB_"+self.institution.upper())
        else :
            return "https://pudb-{}.alma.exlibrisgroup.com/view/sru/{}?version=1.2&operation=searchRetrieve".format(self.institution.lower(),"33PUDB_"+self.institution.upper())

    def fullurl(self):
        return self.baseurl + '&format=marcxml' + '&query=' + self.searchQuery()

    def searchQuery(self):
        if self.complex_query :
            searchQuery = self.query
        else :
            searchQuery = self.index
            searchQuery += self.operator
            searchQuery += self.query
        if not self.noticesSuppr:
            searchQuery += ' and alma.mms_tagSuppressed=false'
        return urllib.parse.quote(searchQuery)

    def sru_request(self):
        url=self.fullurl()
        self.logger.debug("{} :: alma_sru :: {}".format(self.query,url))
        r = requests.get(url)
        try:
            r.raise_for_status()  
        except requests.exceptions.HTTPError:
            self.status = False
            self.logger.error("{} :: {} :: HTTP Status: {} || Method: {} || URL: {} || Response: {}".format(self.query, 
                                                                                                            self.service ,
                                                                                                            r.status_code,
                                                                                                            r.request.method,
                                                                                                            r.url,
                                                                                                            r.text))
            self.error_msg = "{} :: {} :: HTTP Status: {} || Method: {} || URL: {} || Response: {}".format(self.query, 
                                                                                                            self.service ,
                                                                                                            r.status_code,
                                                                                                            r.request.method,
                                                                                                            r.url,
                                                                                                            r.text)
        else:
            self.status = True
            reponse = r.content.decode('utf-8')
            reponsexml = ET.fromstring(reponse)
            return reponsexml

    def get_nombre_resultats(self):
        
        if self.result.findall("sru:numberOfRecords",ns):
            return self.result.find("sru:numberOfRecords",ns).text
        else : 
            return 0
    
    def get_bibliographic_level(self):
        """Analyse le leader pour définir le niveau bibliographique de la ressource (position 06 du Leader). 
        Retourne le libellé et le type d'identifinat bibliographique (idbn ou issn en fonction du niveau de la ressource)

        Args:
            option (string): code, descr ou id

        Returns:
            dict : {"descr" : libellé, "id" = type d'identifiant}
        """
        bibliographic_level = {
                "a" : {
						"descr" : "Monographic component part",
						"id" :  "none"
                        },
                "b" : {
						"descr" : "Serial component part",
						"id" :  "none"
                        },
                "c" : {
						"descr" : "Collection",
						"id" :  "issn"
                        },
                "d" : {
						"descr" : "Subunit",
						"id" :  "none"
                        },
                "i" : {
						"descr" : "Integrating resource",
						"id" :  "none"
                        },
                "m" : {
						"descr" : "Monograph/Item",
						"id" :  "isbn"},
                "s" : {
						"descr" : "Serial",
						"id" :  "issn"}
                }
        leader = self.record.find("marc:leader",ns).text
        return bibliographic_level[leader[7]]

    def get_identifiants_bib(self, convert_to_isbn_treize = True):
        marc_fields = {
            "isbn" : {
                "main" : {
                    "Field" : "020",
                    "Subfield" : "a"
                },
                "other_support" : {
                    "Field" : "776",
                    "Subfield" : "z"
                }
            },
            "issn" : {
                "main" : {
                    "Field" : "022",
                    "Subfield" : "a"
                },
                "other_support" : {
                    "Field" : "776",
                    "Subfield" : "x"
                }
            }
        }
        ids_lists = {
                        "main" : [], 
                        "other_support" : []
                        }
        #On regarde dans le label pour savoir s'il sagit d'un livre ou d'un perio
        bibliographic_level = self.get_bibliographic_level()
        type_identifiant = bibliographic_level["id"]
        if type_identifiant == 'none' :
            return {"bibliographic_level" : bibliographic_level['descr'], "ids_lists" : ids_lists  }
        #On va récupérer les identifiants
        for key in marc_fields[type_identifiant] :
            self.logger.debug(key)
            for id_field in self.record.findall(".//marc:datafield[@tag='{}']/marc:subfield[@code='{}']".format(marc_fields[type_identifiant][key]['Field'],marc_fields[type_identifiant][key]['Subfield']),ns):
                    # Si c'est un isbn on le convertit en isbn 13 si c'est demandé
                    if type_identifiant == "isbn" and convert_to_isbn_treize :
                        isbn_treize = Isbns.convert_10_to_13(id_field.text)
                        ids_lists[key].append(isbn_treize)
                    else :
                        ids_lists[key].append(id_field.text)
                
        return {"bibliographic_level" : bibliographic_level['descr'], "ids_lists" : ids_lists  }

    def get_ppn(self):
        ppn_list = []
        for other_syst_nb_field in self.record.findall(".//marc:datafield[@tag='035']",ns) :
            try : 
                other_syst_nb = other_syst_nb_field.find("marc:subfield[@code='a']",ns).text
            except AttributeError:
                self.logger.debug("Pas de 035 $$a")
                continue
            if other_syst_nb[:5] == "(PPN)" :
                self.logger.debug(other_syst_nb)
                if not other_syst_nb_field.find("marc:subfield[@code='9']",ns) :
                    ppn_list.append(other_syst_nb)
        return ppn_list


               
    