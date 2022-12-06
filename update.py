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

    stops = pd.read_csv('data/lpp/stops.csv', index_col=['id'])
    stopNames = stops['name'].unique()

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
        if nameFrom not in stopNames:
            print(f"Unknown nameFrom '{nameFrom}' stop")
            raise

        nameTo = match.group(4).strip()
        if nameTo not in stopNames:
            print(f"Unknown nameTo '{nameTo}' stop")
            raise

        linesArray.append([val, line, name, nameFrom, nameTo])

    df = pd.DataFrame(linesArray, columns=[
                      'id', 'line', 'name', 'nameFrom', 'nameTo'])
    df.set_index('id', inplace=True)
    # df.sort_values(by=['line'], inplace=True)
    print(df)
    df.to_csv('data/lpp/lines.csv')


def getLppLinesStops():
    lines = pd.read_csv('data/lpp/lines.csv', index_col=['id'])
    stops = pd.read_csv('data/lpp/stops.csv', index_col=['id'])
    linesStopsArray = []

    # "?stop=700012-2&amp;ref=1211"
    # stopHrefRegex = r"^\?stop=([0-9]{6,6})-[0-9]&amp;ref=[0-9]{3,4}$"
    stopHrefRegex = r"^\?stop=([0-9]{6,6})-([0-9]{1,1})"

    for index, row in lines.iterrows():
        print("==========", index, row['line'], row['name'], "==========")
        # https://www.lpp.si/sites/default/files/lpp_vozniredi/iskalnik/index.php?line=1240
        page = requests.get(f'{BaseURL}?line={index}')
        page.raise_for_status()
        soup = BeautifulSoup(page.content, "html.parser")
        direcionsDiv = soup.find("div", {"id": f'line{index}'})
        dirDiv = direcionsDiv.find_all("div", {"class": 'lineDir'})
        for direction in dirDiv:
            dirStops = direction.find_all("div", {"class": "line-dir-stop"})
            dirSequence = 0
            for stopDiv in dirStops:
                stopA = stopDiv.find("a", {"class": 'stop'})
                text = stopA.text.strip()
                href = stopA['href']
                match = re.match(stopHrefRegex, href)
                if match == None:
                    print(
                        f"Unexpected href '{href}' in stop link for {text}, not matching regex '{stopHrefRegex}', aborting.")
                    raise

                stopId = int(match.group(1))
                officialStopName = stops.at[stopId, 'name']
                if officialStopName != text:
                    print(
                        f"Stop name of {stopId} shold be '{officialStopName}' but got '{text}'!")
                    raise ("Stop name mismatch")
                dir = match.group(2)
                if dir != "1" and dir != "2":
                    print(
                        f"Unexpected direction '{dir}' in line '{index}', aborting.")
                    raise ("Unexpected direction")
                dirSequence += 1
                print(index, dir, dirSequence, stopId, text)
                linesStopsArray.append([index, dir, dirSequence, stopId])

    df = pd.DataFrame(linesStopsArray, columns=[
        'lineId', 'direction', 'sequence', 'stopId'])
    df.set_index(['lineId', 'direction', 'sequence'], inplace=True)
    print(df)
    df.to_csv('data/lpp/lines_stops.csv')


if __name__ == "__main__":

    getLppStops()
    getLppLines()
    getLppLinesStops()
