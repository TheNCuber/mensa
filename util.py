#!/usr/bin/env python

import datetime
from zoneinfo import ZoneInfo
from pyopenmensa.feed import LazyBuilder

__all__ = ['xmlEscape', 'StyledLazyBuilder', 'nowZurich']

defaultStyleSheets = ('https://cdn.jsdelivr.net/npm/om-style@1.0.0/basic.css', 'https://cdn.jsdelivr.net/npm/om-style@1.0.0/lightgreen.css')

def xmlEscape(s, escapeDoubleQuotes=False):
    s = str(s).replace('&', '&amp;')  # amp first!
    s = s.replace('>', '&gt;')
    s = s.replace('<', '&lt;')
    if escapeDoubleQuotes:
        s = s.replace('"', '&quot;')
    return s


class StyledLazyBuilder(LazyBuilder):
    def toXMLFeed(self, styles=defaultStyleSheets):
        feed = self.toXML()
        xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n'
        if styles:
            for style in styles:
                xml_header += '<?xml-stylesheet href="' + xmlEscape(style, True) + '" type="text/css"?>\n'
        return xml_header + feed.toprettyxml(indent='  ')

def nowZurich():
    zurich = ZoneInfo('Europe/Zurich')
    now = datetime.datetime.now(tz=zurich)
    return now
