![Latest Release](https://img.shields.io/github/release/VAKazakov/EDMC-Triumvirate.svg)

This ReadMe on other languages: [Русский](README.md), [French](README-FR.md)

![Triumvirate](https://user-images.githubusercontent.com/25157296/117574269-03a3d500-b0e5-11eb-901d-44a4812e2de0.png)

# EDMC-Triumvirate
Triumvirate plugin for EDMC, developed by Close Encounters Corps, is an important part of the overall ecosystem "Gehirn" (server-site-plugin-discord), acts as a universal tool for collecting and processing game data, allows you to track the influence in controlled faction systems, pinpoint tasks for the user on BGS, coordinate the work of pilots, notify colleagues about abnormal situations in long haul flights. In the future, this plugin will receive a number of improvements designed to further optimize the work of pilots in the vastness of the Galaxy.

***Confidential user information, system characteristics and non-public personal data are not collected, stored or processed as a matter of principle.***

# Pay attention:

The functionality is guaranteed on Windows 10 and Windows 11 systems. The EDMC Triumvirate plugin is strongly NOT compatible with the EDMC-Canonn plugin, EDMC-USS-Survey and the outdated EDMC-USS-Survey-Triumvirate-edition. The EDMC-Canonn plugin was originally integrated into Triumvirate, and we have also integrated support for Discord Presence, FCMC and the transfer of collected scientific data not only to Canonn servers, but also to the addresses of other scientific organizations. A system of issuing and accounting for completed missions within the framework of the activity against the Club is working.

# Plugin features (will be updated as improvements are made)

## Element for receiving commands from the user

### The /sos command

After the pilot will write in the game chat command "/sos" (in any register), the plugin will generate and send to the faction discord chat* (in a specially designated channel) a data packet with the location, amount of fuel, location and time to empty tank. Thanks to this data, a pilot in a dangerous situation will be able to get fuel and will be refueled in a timely manner.

\*If you are an independent pilot (according to the plugin), your request for help will be forwarded to Close Encounters Corps

## Element of the orienteering system (aka Patrol)

The guidance system is used to navigate to points of interest and includes:

* Location of your ships. A tool that gives real-time information about the location of your ships. Adding a compass/GPS-like function for visual flight to points of interest is under development.
* Automation and transfer of all system functions to track fractional influence levels in controlled systems for analysis and processing to fractional servers is in the works. This tool provides a brief informational summary of the state of the systems with our faction presence. For faction leaders there is a function of manual assignment of tasks for specific systems to be issued directly to the plugin and the possibility of semi-automatic issuance of tasks for the curbing of negative statuses.
* We are working on adding the function of orbital navigation and following the specified coordinates with the output of reference information about the known points of the route.
* Working on adding a function to send data about the commander's ships to the server and the site to give location information on the interactive map in real/ pseudo-real time.
* Adding a feature to give out information about your carrier ship's location, list of its characteristics and fuel tank fill-up is under development.
* Adding a "friend-or-foe" identification system to determine if you are facing a partner, ally, or enemy/neutral.
* Working on adding a distance-to-behind feature to the SRV. 

## The news hub element

Allows you to read the latest news and current information on the Galaxy.

## Element on Targoid Interception reports

Allows you to collect and analyze information about the time and location of Targoid interceptions of your ships. Used to accurately estimate the scale of an alien invasion.

## The Targoid Elimination Analysis Element

Collects and processes information about the time, location, type and number of downed Targoid ships. Used to summarize the results of the week and build a clear plan to counter alien invasion. The function transmits all collected information to the faction servers for processing and transferring to the interactive tables on the faction website.

## Element on NHSS reports

Collects and analyzes information about detected alien signals.

## Element on FSS reports

Collects and analyzes complete information about the current system.

## The Codex Element

Collects log entry information and voluntarily synchronizes it with external scientific services, such as [Canonn database](https://api.canonn.tech/documentation).

## Element on analyzing information from the pilot's journal

Collects and processes information from the logbook. Provides updates on markets, commodities, and prices. Helps all pilots get up-to-date data. Transmits received information to INARA, EDSM, EDDB and similar profile systems.

## Element for the collection of information about fleet-carriers

Collects and processes information about a specific pilot's carrier ship. Provides updates to the FCMC website, and allows you to display, in near real time, the carrier ships of faction pilots on an interactive map on the faction website. Helps all pilots get up-to-date data. Transmits received information to INARA, EDSM, EDDB, and similar profile systems.

## Element on changing the plugin interface depending on the faction of the user

Functions for changing the design style of the plugin window to match the style of a particular faction.

## Installation Instructions:

1) Download and install the latest version of [EDMarketConnector](https://github.com/Marginal/EDMarketConnector/blob/rel-342/README.md#installation) (if it is already installed, be sure to check EDMC for updates)

2) Download the latest [EDMC-Triumvirate](https://github.com/Close-Encounters-Corps/EDMC-Triumvirate/releases/latest) plugin release by clicking "Source code (zip)"

3) Unpack the downloaded archive into the folder `%USERPROFILE%\AppData\Local\EDMarketConnector\plugins` (you can paste this into the file explorer address bar)

4) Launch EDMC. If you see a window [like this](https://cdn.discordapp.com/attachments/518418556615000074/590004329692397579/unknown.png) then go to step 5, otherwise you will need to verify the installation is correct

5) ***You're awesome!***

## Development
The plugin works on the Python version provided by EDMC; currently it's Python 3.11.
How to prepare the environment for development:
```bash
pip install -r requirements-dev.txt
pre-commit install
```

## Disclaimer
EDMC-Triumvirate was created using assets and imagery from Elite Dangerous, with the permission of Frontier Developments plc, for non-commercial purposes. It is not endorsed by nor reflects the views or opinions of Frontier Developments and no employee of Frontier Developments was involved in the making of it.

EDMC-Triumvirate uses data from [Canonn API V2](https://docs.canonn.tech), [ED Star Map (EDSM)](https://www.edsm.net/), [Elite BGS](https://elitebgs.app/), with permision of their owners.

EDMC-Triumvirate is based on [EDMC-Canonn](https://github.com/canonn-science/EDMC-Canonn), with permission of initial developers.

All Contents Copyright ©️ 2016-2025 Close Encounters Corps, Triumvirate. KAZAK0V, AntonyVern, Osmium, Elcy (rinkulu), Evil-Horse, Art-py. All Rights Reserved.

Logo - Anton Vernitskiy aka AntonyVern/Automatic system
