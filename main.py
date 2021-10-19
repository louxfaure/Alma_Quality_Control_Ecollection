#!/usr/bin/python3
# -*- coding: utf-8 -*-
# from Alma_Apis_Interface import 
import json
import os
import re
from datetime import date, timedelta
import logging
import logs
import AlmaSru
import Bacon
# import AlmaApi
# import mail

SERVICE = "Alma_Quality_Control_Ecollection"
INSTANCE = 'Test'
INSTITUTION = 'BXSA'

BACON_PACKAGE = 'CAIRN_GLOBAL_POCHES-GENERAL'
ECOLLECTION = ""
ESERVICE = ""

#On initialise le logger
logs.init_logs(os.getenv('LOGS_PATH'),SERVICE,'DEBUG')
logger = logging.getLogger(SERVICE)

# On récupère la clef d'API
api_key = ""

if INSTANCE == 'Test' :
    api_key = os.getenv("TEST_{}_API".format(INSTITUTION))
else :
    api_key = os.getenv("PROD_{}_BIB_API".format(INSTITUTION))

# pid = '5321810050004676'
# result = AlmaSru.AlmaSru( pid, 'alma.portfolio_pid', operator = '==' , noticesSuppr=False, complex_query=False, institution = INSTITUTION, service= SERVICE,instance=INSTANCE)
# if result.status :
#     ids_bibs = result.get_identifiants_bib(convert_to_isbn_treize = True)
#     logger.debug(ids_bibs)

kbart_bacon = Bacon.Bacon_Package(BACON_PACKAGE, SERVICE)