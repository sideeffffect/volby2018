#!/usr/bin/env python3

# GPLv3+

import csv
from requests import get
from io import BytesIO, TextIOWrapper
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import sys

RZCOCO_ARCHIVE_URL = "https://www.volby.cz/opendata/kv2018/KV2018reg20181008_csv.zip"
RZCOCO_FILENAME = "kvrzcoco.csv"
MUNICIPALITY_RESULTS_URL_TEMPLATE = "https://www.volby.cz/pls/kv2018/vysledky_obec?cislo_obce=%s"
MUNICIPALITY_CODE_COLUMN = "KODZASTUP"
FIELD_NAMES = ['KODZASTUP', 'NAZEVZAST', 'OZNAC_TYPU', 'VOLENO_ZASTUP', 'POCET_OBVODU', 'JE_SPOCTENO' ,'OKRSKY_CELKEM', 'OKRSKY_ZPRAC', 'OKRSKY_ZPRAC_PROC', 'ZAPSANI_VOLICI', 'VYDANE_OBALKY', 'UCAST_PROC', 'ODEVZDANE_OBALKY', 'PLATNE_HLASY' ,'POR_STR_HLAS_LIST', 'VSTRANA', 'NAZEV_STRANY', 'HLASY', 'HLASY_PROC', 'KANDIDATU_POCET', 'ZASTUPITELE_POCET', 'ZASTUPITELE_PROC', 'PORADOVE_CISLO', 'JMENO', 'PRIJMENI', 'TITULPRED', 'TITULZA', 'HLASY', 'HLASY_PROC']
OUTPUT_FILE_NAME = 'volby.results.csv'

def getMunicipalityRegister(rzcocoArchiveUrl, rzcocoFilename):
  request = get(rzcocoArchiveUrl)
  zip_file = ZipFile(BytesIO(request.content))
  fileraw = zip_file.open(rzcocoFilename, 'r')
  csvfile = TextIOWrapper(fileraw, encoding="windows-1250")
  csvreader = csv.DictReader(csvfile, delimiter = ';')
  return csvreader


def getMunicipalityResults(municipalityCode):
  municipalityResultsUrl = MUNICIPALITY_RESULTS_URL_TEMPLATE % (str(municipalityCode))
  request = get(municipalityResultsUrl)
  results = ET.fromstring(request.content)
  return results


def flattenParty(municipDict, participDict, d):
  partyDict = d.attrib
  bigDict = {**municipDict, **participDict, **partyDict}
  representatives = list(d)
  if not representatives:
    return [bigDict]
  else:
    return list(map(lambda represent: {**bigDict, **represent.attrib}, representatives))


def flattenMunicipalResults(municipalResults):
  municipDict = municipalResults[0].attrib
  participDict = municipalResults[0][0][0].attrib
  parties = list(map(lambda d: flattenParty(municipDict, participDict, d), municipalResults[0][0][1:]))
  return sum(parties, [])


def main():
  municipalityRegister = getMunicipalityRegister(RZCOCO_ARCHIVE_URL, RZCOCO_FILENAME)
  municipalityCodes = list(map(lambda row: row[MUNICIPALITY_CODE_COLUMN], municipalityRegister))
  with open(OUTPUT_FILE_NAME, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=FIELD_NAMES)
    writer.writeheader()
    i = 1
    size = len(municipalityCodes)
    for code in municipalityCodes:
      print("%s\t%d/%d\t%f %%" % (code, i, size, 100*i/size))
      i = i+1
      try:
        municipalResults = getMunicipalityResults(code)
        flatMunicipalResults = flattenMunicipalResults(municipalResults)
        for row in flatMunicipalResults:
          writer.writerow(row)
      except Exception as inst:
        sys.stderr.write("Error in processing %s\n%s\n\n" % (str(code), str(inst)))


if __name__ == "__main__":
    main()

