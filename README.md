# mensa
Parsers for openmensa.org. The parsers runs in a [Github action](https://github.com/TheNCuber/mensa/actions?query=workflow%3ARunParsers) and push the XML feeds to [Github pages](https://thencuber.github.io/mensa/)

Parsers support:
*   [University of Bern](https://www.gastro-unibern.ch/)
*   [University of Fribourg](https://www.unifr.ch/mensa/)

|  Feeds       |                                         Status                                                                                                                  |                     Cron                                                                                                                                      |
|:------------:|:---------------------------------------------------------------------------------------------------------------------------------------------------------------:|:-------------------------------------------------------------------------------------------------------------------------------------------------------------:|
| today        | [![RunParsersToday](https://github.com/thencuber/mensa/workflows/RunParsersToday/badge.svg)](https://github.com/thencuber/mensa/actions?query=workflow%3ARunParsersToday) | [32 6-11 * * 1-5](https://crontab.guru/#28_6-11_*_*_1-5 "“At minute 28 past every hour from 6 through 11 on every day-of-week from Monday through Friday.” ") |
| all          | [![RunParsers](https://github.com/thencuber/mensa/workflows/RunParsers/badge.svg)](https://github.com/thencuber/mensa/actions?query=workflow%3ARunParsers)                | [8 6 * * *](https://crontab.guru/#8_6_*_*_* "“At 06:08.” ")                                                                                                 |

Links:
*   See the resulting feeds at [https://thencuber.github.io/mensa/](https://thencuber.github.io/mensa/)
*   [Understand OpenMensa’s Parser Concept](https://doc.openmensa.org/parsers/understand/)
*   OpenMensa [XML schema](https://doc.openmensa.org/feed/v2/)
*   OpenMensa Android app on [f-droid](https://f-droid.org/en/packages/de.uni_potsdam.hpi.openmensa/), [playstore](https://play.google.com/store/apps/details?id=de.uni_potsdam.hpi.openmensa), [GitHub](https://github.com/domoritz/open-mensa-android)

Acknowledgment:
* Much of the code, structure and workflows for this repository were directly copied from [cvzi/mensa](https://github.com/cvzi/mensa) which is licensed under the MIT license.
