import sys
import os
import json
import logging
import urllib
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import decimal

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

baseUrl = 'https://www.unifr.ch/mensa/de/'

s = requests.Session()
s.headers = {
    'User-Agent': f'{useragentname}/{__version__} ({useragentcomment}) {requests.utils.default_user_agent()}'
}


class Parser:
    def feed(self, refName):
        if refName not in self.canteens:
            return f"Unkown canteen '{refName}'"
        lazyBuilder = StyledLazyBuilder()
        r = s.get(baseUrl)
        soup = BeautifulSoup(r.content, "html.parser")
        weeks = soup.find_all("div", class_="inner-5")
        for week in weeks:
            days = week.find_all("a", {"data-tabcordion-toggler" : re.compile(r'tab-[0-9]')})
            for day in days:
                date = datetime.strptime(day.text[3:] + '.' + datetime.now().strftime('%Y'), '%d.%m.%Y') #TODO Test Servertime
                dayPlan = week.find("div", {"data-accordion-content" : day['data-tabcordion-toggler']})
                dailyMenus = dayPlan.find("h3", string=self.canteens[refName]["source"]).parent.find_all("a", class_="menu-item")
                for menu in dailyMenus:
                    mealCategory = menu.find("h5").find(text=True,recursive=False).strip()
                    mealPrice = int(decimal.Decimal(menu.find("small").find(text=True,recursive=False).strip()) * 100)
                    dirtyMealFragments = []
                    for sibling in menu.find("h5").next_siblings:
                        if(sibling.text.strip()):
                            for linebreak in sibling.find_all("br"):
                                linebreak.replace_with("|" + linebreak.text.strip() + "|")
                            for dirtyMealFragment in sibling.text.strip().split("|"):
                                dirtyMealFragments.append(dirtyMealFragment)
                    mealFragments = []        
                    for dirtyMealFragment in dirtyMealFragments:
                        if(dirtyMealFragment.strip()):
                            mealFragments.append(dirtyMealFragment.strip())
                    mealName = " | ".join(mealFragments)
                    mealPrices = { "other": mealPrice }

                    lazyBuilder.addMeal(date.isoformat(),
                                        mealCategory,
                                        mealName,
                                        "",
                                        mealPrices)

                    # Clear meal variables
                    mealCategory = ""
                    mealName = ""
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
        "http://localhost/{metaOrFeed}/unibe_{mensaReference}.xml").feed("perolles"))
