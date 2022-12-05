#!./venv/bin/python

import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

BaseURL = "https://www.lpp.si/sites/default/files/lpp_vozniredi/iskalnik/index.php"


def getLppStops():
    page = requests.get(BaseURL)
    # print(page)
    page.raise_for_status()
    soup = BeautifulSoup(page.content, "html.parser")

    stopTextRegex = r"^(.*) \(([0-9]{6,6})\)$"

    selectListStops = soup.find("select", {"id": "stop"})
    # print(selectListStops)
    stopsArray = []
    stopsOptions = selectListStops.find_all('option')
    for stopOption in stopsOptions:
        val = stopOption['value']
        if val == "":
            continue
        text = stopOption.text.strip()
        match = re.match(stopTextRegex, text)
        if match == None:
            print(
                f"Unexpected text '{text}' in stop option, not matching regex '{stopTextRegex}', aborting.")
            raise

        name = text[:-len(val)-3].strip()
        stopsArray.append([val, name])

    df = pd.DataFrame(stopsArray, columns=['id', 'name'])
    df.sort_values(by=['name', 'id'], inplace=True)
    df.set_index('id', inplace=True)
    print(df)
    df.to_csv('data/lpp/stops.csv')


def getLppLines():
    page = requests.get(BaseURL)
    page.raise_for_status()
    soup = BeautifulSoup(page.content, "html.parser")

    # 11B - BEŽIGRAD (Železna) - ZALOG
    lineTextRegex = r"^([0-9A-Z]{1,3}) - ((.*) - (.*))$"

    selectListLines = soup.find("select", {"id": "line"})
    linesArray = []
    linesOptions = selectListLines.find_all('option')
    for stopOption in linesOptions:
        val = stopOption['value']
        if val == "":
            continue
        text = stopOption.text.strip()
        match = re.match(lineTextRegex, text)
        if match == None:
            print(
                f"Unexpected text '{text}' in stop option, not matching regex '{lineTextRegex}', aborting.")
            raise

        line = match.group(1).strip()
        name = match.group(2).strip()
        nameFrom = match.group(3).strip()
        nameTo = match.group(4).strip()
        linesArray.append([val, line, name, nameFrom, nameTo])

    df = pd.DataFrame(linesArray, columns=[
                      'id', 'line', 'name', 'nameFrom', 'nameTo'])
    df.set_index('id', inplace=True)
    # df.sort_values(by=['line'], inplace=True)
    print(df)
    df.to_csv('data/lpp/lines.csv')


if __name__ == "__main__":

    getLppStops()
    getLppLines()
