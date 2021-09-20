import sys
import os
import json
import logging
import urllib
import re
import requests
import html

try:
    from version import __version__, useragentname, useragentcomment
    from util import StyledLazyBuilder
except ModuleNotFoundError:
    include = os.path.relpath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, include)
    from version import __version__, useragentname, useragentcomment
    from util import StyledLazyBuilder

metaJson = os.path.join(os.path.dirname(__file__), "canteenDict.json")

metaTemplateFile = os.path.join(os.path.dirname(__file__), "metaTemplate.xml")

weekdaysMap = [
    ("Mo", "monday"),
    ("Di", "tuesday"),
    ("Mi", "wednesday"),
    ("Do", "thursday"),
    ("Fr", "friday"),
    ("Sa", "saturday"),
    ("So", "sunday")
]

legend = {
    'A': 'Glutenhaltiges Getreide',
    'B': 'Krebstiere',
    'C': 'Eier',
    'D': 'Fisch',
    'E': 'Erdnüsse',
    'F': 'Soja',
    'G': 'Milch',
    'H': 'Hartschalenobst (Nüsse)',
    'L': 'Sellerie',
    'M': 'Senf',
    'N': 'Sesam',
    'O': 'Schwefeldioxid und Sulfite',
    'P': 'Lupine',
    'R': 'Weichtiere',
}

baseUrl = 'https://cms.zfv.ch/food-getter.php'

s = requests.Session()
s.headers = {
    'User-Agent': f'{useragentname}/{__version__} ({useragentcomment}) {requests.utils.default_user_agent()}'
}


class Parser:
    def feed(self, refName):
        if refName not in self.canteens:
            return f"Unkown canteen '{refName}'"
        url = baseUrl + self.canteens[refName]["source"]
        lazyBuilder = StyledLazyBuilder()
        lazyBuilder.setLegendData(legend)
        r = s.get(url)
        dictonary = json.loads(r.json()[0])
        for weeklyPlan in dictonary["Wochenspeiseplaene"]:
            # FOR DEBUGGING PURPOSES
            # print("Wochenplan:")
            # print("Kalenderwoche " + str(weeklyPlan["Kalenderwoche"]))
            # print("Startdatum: " + str(weeklyPlan["StartDatum"]))
            # print("Enddatum: " + str(weeklyPlan["EndDatum"]))
            # print("Jahr: " + str(weeklyPlan["Jahr"]))
            # print("Text oben: " + str(weeklyPlan["TextOben"]))
            # print("Text unten: " + str(weeklyPlan["TextUnten"]))
            for dailyPlan in weeklyPlan["Tagesspeiseplaene"]:
                mealDate = dailyPlan["Datum"]
                for dailyPlanPosition in dailyPlan["TagesspeiseplanPositionen"]:
                    mealFragments = []
                    dirtyMealFragments = dailyPlanPosition["Menue"]["Bezeichnung"].split("<br/>")
                    for dirtyMealFragment in dirtyMealFragments:
                        mealFragment = html.unescape(dirtyMealFragment).strip(', ')
                        mealFragments.append(mealFragment)
                    mealName = " | ".join(mealFragments)
                    mealCategory = dailyPlanPosition["Menuegruppe"]["Bezeichnung"]
                    if len(dailyPlanPosition["Menue"]["Preise"]) < 1:
                        continue
                    if len(dailyPlanPosition["Menue"]["Preise"]) == 1:
                        mealPrices = {
                            "student": int(dailyPlanPosition["Menue"]["Preise"][0]["Preis"] * 100),
                            "other": int(dailyPlanPosition["Menue"]["Preise"][0]["Preis"] * 100)
                        }
                    if len(dailyPlanPosition["Menue"]["Preise"]) > 1:
                        mealPrices = {
                            "student": int(dailyPlanPosition["Menue"]["Preise"][0]["Preis"] * 100),
                            "other": int(dailyPlanPosition["Menue"]["Preise"][1]["Preis"] * 100)
                        }
                    mealNotes = []
                    if len(dailyPlanPosition["Menue"]["Symbole"]) > 0:
                        symbols = sorted(dailyPlanPosition["Menue"]["Symbole"], key=lambda k: k['Reihenfolge'])
                        for symbol in symbols:
                            mealNotes.append(symbol["Bezeichnung"])
                    if dailyPlanPosition["Menue"]["Herkunft"]:
                        mealNotes.append("Herkunft " + str(dailyPlanPosition["Menue"]["Herkunft"]))
                    if len(dailyPlanPosition["Menue"]["Allergene"]) > 0:
                        allergenString = "Allergene:"
                        for allergen in dailyPlanPosition["Menue"]["Allergene"]:
                            allergenString += (" " + allergen["Bezeichnung"] + ",")
                        allergenString = allergenString[:-1]
                        mealNotes.append(allergenString)

                    lazyBuilder.addMeal(mealDate,
                                        mealCategory,
                                        mealName,
                                        mealNotes,
                                        mealPrices)

                    # Clear meal variables
                    mealCategory = ""
                    mealName = ""
                    mealNotes = []
                    mealPrices = {}

        return lazyBuilder.toXMLFeed()

    def meta(self, refName):
        """Generate an openmensa XML meta feed from the static json file using an XML template"""
        with open(metaTemplateFile) as f:
            template = f.read()

        for reference, mensa in self.canteens.items():
            if refName != reference:
                continue

            data = {
                "name": mensa["name"],
                "address": mensa["address"],
                "city": mensa["city"],
                "phone": mensa['phone'],
                "latitude": mensa["latitude"],
                "longitude": mensa["longitude"],
                "feed": self.urlTemplate.format(metaOrFeed='feed', mensaReference=urllib.parse.quote(reference)),
                "source": baseUrl + mensa["source"],
            }
            openingTimes = {}
            pattern = re.compile(
                r"([A-Z][a-z])(\s*-\s*([A-Z][a-z]))?\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2}) Uhr")
            m = re.findall(pattern, mensa["times"])
            for result in m:
                fromDay, _, toDay, fromTimeH, fromTimeM, toTimeH, toTimeM = result
                openingTimes[fromDay] = "%02d:%02d-%02d:%02d" % (
                    int(fromTimeH), int(fromTimeM), int(toTimeH), int(toTimeM))
                if toDay:
                    select = False
                    for short, long in weekdaysMap:
                        if short == fromDay:
                            select = True
                        elif select:
                            openingTimes[short] = "%02d:%02d-%02d:%02d" % (
                                int(fromTimeH), int(fromTimeM), int(toTimeH), int(toTimeM))
                        if short == toDay:
                            select = False

                for short, long in weekdaysMap:
                    if short in openingTimes:
                        data[long] = 'open="%s"' % openingTimes[short]
                    else:
                        data[long] = 'closed="true"'
            for key in data:
                data[key] = data[key]
            xml = template.format(**data)
            return xml

        return '<openmensa xmlns="http://openmensa.org/open-mensa-v2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.1" xsi:schemaLocation="http://openmensa.org/open-mensa-v2 http://openmensa.org/open-mensa-v2.xsd"/>'

    def __init__(self, urlTemplate):
        with open(metaJson, 'r', encoding='utf8') as f:
            self.canteens = json.load(f)

        self.urlTemplate = urlTemplate

    def json(self):
        tmp = {}
        for reference in self.canteens:
            tmp[reference] = self.urlTemplate.format(
                metaOrFeed='meta', mensaReference=urllib.parse.quote(reference))
        return json.dumps(tmp, indent=2)


def getParser(urlTemplate):
    return Parser(urlTemplate)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(getParser(
        "http://localhost/{metaOrFeed}/unibe_{mensaReference}.xml").feed("gesellschaftsstrasse"))
