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
    df.to_csv('data/lpp/stops.csv', encoding='utf-8-sig')


def getLppLines():
    page = requests.get(BaseURL)
    page.raise_for_status()
    soup = BeautifulSoup(page.content, "html.parser")

    # 11B - BEŽIGRAD (Železna) - ZALOG
    # "13 V pripravi - C. STOŽICE P+R - SOSTRO" - ignore!
    # 18 Počitniški - KOLODVOR - C. STOŽICE P+R
    # 11B Počitniški - BEŽIGRAD (Železna) - ZALOG
    # SŽ - SŽ ŠIŠKA - SŽ KOLODVOR
    # 24 Počitniški - BTC-ATLANTIS - VEVČE
    lineTextRegex = r"^([^ ]*)( ([^\-]*))? - ((.*) - (.*))$"

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
                f"Unexpected text '{text}' in line option, not matching regex '{lineTextRegex}', skipping.")
            continue
            # raise

        line = match.group(1).strip()
        lineExtra = match.group(3)
        nameFrom = match.group(5).strip()
        if nameFrom not in stopNames:
            print(f"Unknown nameFrom '{nameFrom}' stop in line {val}")
            raise

        nameTo = match.group(6).strip()
        if nameTo not in stopNames:
            print(f"Unknown nameTo '{nameTo}' stop in line {val}")
            raise

        linesArray.append([val, line, lineExtra, nameFrom, nameTo])

    df = pd.DataFrame(linesArray, columns=[
                      'id', 'line', 'lineExtra', 'nameFrom', 'nameTo'])
    df.set_index('id', inplace=True)
    # df.sort_values(by=['line'], inplace=True)
    print(df)
    df.to_csv('data/lpp/lines.csv', encoding='utf-8-sig')


def getLppLinesStops():
    lines = pd.read_csv('data/lpp/lines.csv', index_col=['id'])
    stops = pd.read_csv('data/lpp/stops.csv', index_col=['id'])
    linesStopsArray = []

    # "?stop=700012-2&amp;ref=1211" - urlencoded, but decoded when reading:
    stopHrefRegex = r"^\?stop=([0-9]{6,6})-(1|2)&lref=[0-9A-Z]{1,3}$"

    for index, row in lines.iterrows():
        print(f"Stops on line {row['line']}/{row['lineExtra']} ({index}): \t{row['nameFrom']} - {row['nameTo']}")
        # https://www.lpp.si/sites/default/files/lpp_vozniredi/iskalnik/index.php?stop=0&l=3B
        page = requests.get(f'{BaseURL}?stop=0&l={index}')
        page.raise_for_status()
        soup = BeautifulSoup(page.content, "html.parser")
        # direcionsDiv = soup.find("div", {"id": f'line{index}'})
        dirDiv = soup.find_all("div", {"class": 'line-dir-wrapper'})
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
                if officialStopName.lower() != text.lower():
                    print(
                        f"Stop name of {stopId} on line  {row['line']}, direction {dir}, sequence {dirSequence} shold be '{officialStopName}' but got '{text}'!")
                    raise ("Stop name mismatch")
                dir = match.group(2)
                dirSequence += 1
                # print(index, dir, dirSequence, stopId, text)
                linesStopsArray.append([index, dir, dirSequence, stopId])

    df = pd.DataFrame(linesStopsArray, columns=[
        'lineId', 'direction', 'sequence', 'stopId'])
    df.set_index(['lineId', 'direction', 'sequence'], inplace=True)
    print(df)
    df.to_csv('data/lpp/lines_stops.csv', encoding='utf-8-sig')


def saveurl(url: str, filename: str):
    print("Downloading ", url)
    r = requests.get(url, allow_redirects=True)
    r.raise_for_status()
    open(filename, 'wb').write(r.content)
    print("Saved", filename)

def getMarpromData():
    saveurl("https://www.marprom.si/webmap/lineData/mainlines.geojson", "data/marprom/mainlines.geojson")
    saveurl("https://www.marprom.si/webmap/lineData/stops.geojson", "data/marprom/stops.geojson")

if __name__ == "__main__":

    getLppStops()
    getLppLines()
    getLppLinesStops()

    getMarpromData()
