import argparse
import requests
import bs4
import time
import re
import subprocess
import sys
import os
import logging
import datetime
import ctypes
from colorama import init, Fore

init()

logging.basicConfig(filename="idlemaster.log", filemode="w",
                    format="[ %(asctime)s ] %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p", level=logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
console.setFormatter(
    logging.Formatter("[ %(asctime)s ] %(message)s", "%m/%d/%Y %I:%M:%S %p"))
logging.getLogger('').addHandler(console)

if sys.platform.startswith('win32'):
    ctypes.windll.kernel32.SetConsoleTitleA("Idle Master")

logging.warning(Fore.GREEN + "WELCOME TO IDLE MASTER" + Fore.RESET)


class SteamIdle(object):

    def __init__(self):
        self.auth_data = {}
        self._parse_args()
        self.read_config(self.args.config)
        self.steam_profile_url = "http://steamcommunity.com/profiles/{}".format(self.auth_data["steamLogin"][:17])
        self.blacklist = []
        self.cookie = self.generate_cookie()
        self.games_to_idle = []

    def _parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--config', required=True, help="Path to SteamIdle config file")
        self.args = parser.parse_args()

    def read_config(self, config_file):
        try:
            with open(config_file, 'r') as fp:
                for line in fp:
                    k, v = line.split('=')
                    self.auth_data[k.strip()] = v.replace('"', '').strip()

        except OSError as e:
            logging.warning(Fore.RED + "Error loading config file {0}".format(e) + Fore.RESET)
            sys.exit(1)

        if not self.auth_data["sessionid"]:
            logging.warning(Fore.RED + "No sessionid set" + Fore.RESET)
            sys.exit(1)

        if not self.auth_data["steamLogin"]:
            logging.warning(Fore.RED + "No steamLogin set" + Fore.RESET)
            sys.exit(1)

    def get_blacklist(self):
        try:
            with open('blacklist.txt', 'r') as fp:
                for line in fp:
                    self.blacklist.append(int(line.strip()))
        except OSError:
            logging.warning("No games have been blacklisted")

    def generate_cookie(self):
        return dict(sessionid=self.auth_data["sessionid"],
                    steamLogin=self.auth_data["steamLogin"],
                    steamparental=self.auth_data["steamparental"])

    def get_games(self):
        """
        Finds games that have card drops remaining
        returns a generator
        :return:
        """

        r = requests.get(self.steam_profile_url + "/badges/", cookies=self.cookie)
        badge_page = bs4.BeautifulSoup(r.text)
        badge_set = badge_page.find_all("div", {"class": "badge_title_stats"})

        for badge in badge_set:
            if badge.find_all("div", {"class": "badge_title_playgame"}):
                print("vvvvvvv")
                #steam://run/368020
                appid = badge.find('a', {"class": "btn_green_white_innerfade"}).get("href").split('/')[-1]
                #num card drops remaining
                drops_remaining = badge.find('span', {"class": "progress_info_bold"}).text.split()[0]
                yield SteamGame(appid, drops_remaining)


class SteamGame(object):

    def __init__(self, appid, remaining_drops):
        self.appid = appid
        self.name = None
        self.remaining_drops = remaining_drops
        self.open = False
        self.start_idle_time = 0
        self.idle_pid = 0

    def get_app_name(self):
        try:
            api = requests.get(
                "http://store.steampowered.com/api/appdetails/?appids={0}&filters=basic".format(self.appid))
            api_data = api.json()
            self.name = api_data[str(appID)]["data"]["name"]
        except requests.RequestException:
            self.name = self.appid

    def idle_open(self):

        try:
            logging.warning("Starting game {0} to idle cards".format(self.name))
            self.start_idle_time = time.time()

            if sys.platform.startswith('win32'):
                process_idle = subprocess.Popen("steam-idle.exe " + str(appID))
            elif sys.platform.startswith('darwin'):
                process_idle = subprocess.Popen(["./steam-idle", str(appID)])
            elif sys.platform.startswith('linux'):
                process_idle = subprocess.Popen(
                    ["python2", "steam-idle.py", str(appID)])
        except:
            logging.warning(
                Fore.RED + "Error launching steam-idle with game ID " + str(appID) + Fore.RESET)
            input("Press Enter to continue...")
            sys.exit()

    def dropDelay(self):
        if self.remaining_drops > 1:
            baseDelay = (15 * 60)
        else:
            baseDelay = (5 * 60)
        return baseDelay




    def idleClose(appID):
        try:
            logging.warning("Closing game " + getAppName(appID))
            process_idle.terminate()
            total_time = int(time.time() - idle_time)
            logging.warning(getAppName(appID) + " took " + Fore.GREEN +
                        str(datetime.timedelta(seconds=total_time)) + Fore.RESET + " to idle.")
        except:
            logging.warning(Fore.RED + "Error closing game. Exiting." + Fore.RESET)
            input("Press Enter to continue...")
            sys.exit()


    def chillOut(appID):
        logging.warning("Suspending operation for " + getAppName(appID))
        idleClose(appID)
        stillDown = True
        while stillDown:
            logging.warning("Sleeping for 5 minutes.")
            time.sleep(5 * 60)
            try:
                rBadge = requests.get(
                    myProfileURL + "/gamecards/" + str(appID) + "/", cookies=cookies)
                indBadgeData = bs4.BeautifulSoup(rBadge.text)
                badgeLeftString = indBadgeData.find_all(
                    "span", {"class": "progress_info_bold"})[0].contents[0]
                if "card drops" in badgeLeftString:
                    stillDown = False
            except:
                logging.warning("Still unable to find drop info.")
    # Resume operations.
        idleOpen(appID)


#
# userinfo = badgePageData.find("div", {"class": "user_avatar"})
# if not userinfo:
#     logging.warning(
#         Fore.RED + "Invalid cookie data, cannot log in to Steam" + Fore.RESET)
#     input("Press Enter to continue...")
#     sys.exit()
#
# if authData["sort"] == "mostvalue" or authData["sort"] == "leastvalue":
#     logging.warning("Getting card values, please wait...")
#
# for badge in badgeSet:
#     print("vvvvvv")
#     print(badge)
#     input("^^^^^")
#     try:
#         badge_text = badge.get_text()
#         dropCount = badge.find_all(
#             "span", {"class": "progress_info_bold"})[0].contents[0]
#         has_playtime = re.search("[0-9\.] hrs on record", badge_text) is not None
#
#         if "No card drops" in dropCount or (has_playtime == False and authData["hasPlayTime"].lower() == "true"):
#             continue
#         else:
#             # Remaining drops
#             dropCountInt, junk = dropCount.split(" ", 1)
#             dropCountInt = int(dropCountInt)
#             linkGuess = badge.find_parent().find_parent().find_parent().find_all(
#                 "a")[0]["href"]
#             junk, badgeId = linkGuess.split("/gamecards/", 1)
#             badgeId = int(badgeId.replace("/", ""))
#             if badgeId in blacklist:
#                 logging.warning(
#                     getAppName(badgeId) + " on blacklist, skipping game")
#                 continue
#             else:
#                 if authData["sort"] == "mostvalue" or authData["sort"] == "leastvalue":
#                     gameValue = requests.get(
#                         "http://api.enhancedsteam.com/market_data/average_card_price/?appid=" + str(badgeId) + "&cur=usd")
#                     push = [badgeId, dropCountInt, float(str(gameValue.text))]
#                     badgesLeft.append(push)
#                 else:
#                     push = [badgeId, dropCountInt, 0]
#                     badgesLeft.append(push)
#     except:
#         continue
#
# logging.warning("Idle Master needs to idle " + Fore.GREEN +
#                 str(len(badgesLeft)) + Fore.RESET + " games")
#
#
# def getKey(item):
#     if authData["sort"] == "mostcards" or authData["sort"] == "leastcards":
#         return item[1]
#     elif authData["sort"] == "mostvalue" or authData["sort"] == "leastvalue":
#         return item[2]
#     else:
#         return item[0]
#
# sortValues = ["", "mostcards", "leastcards", "mostvalue", "leastvalue"]
# if authData["sort"] in sortValues:
#     if authData["sort"] == "":
#         games = badgesLeft
#     if authData["sort"] == "mostcards" or authData["sort"] == "mostvalue":
#         games = sorted(badgesLeft, key=getKey, reverse=True)
#     if authData["sort"] == "leastcards" or authData["sort"] == "leastvalue":
#         games = sorted(badgesLeft, key=getKey, reverse=False)
# else:
#     logging.warning(Fore.RED + "Invalid sort value" + Fore.RESET)
#     input("Press Enter to continue...")
#     sys.exit()
#
# for appID, drops, value in games:
#     delay = dropDelay(int(drops))
#     stillHaveDrops = 1
#     numCycles = 50
#     maxFail = 2
#
#     idleOpen(appID)
#
#     logging.warning(
#         getAppName(appID) + " has " + str(drops) + " card drops remaining")
#
#     if sys.platform.startswith('win32'):
#         ctypes.windll.kernel32.SetConsoleTitleA(
#             "Idle Master - Idling " + getPlainAppName(appID) + " [" + str(drops) + " remaining]")
#
#     while stillHaveDrops == 1:
#         try:
#             logging.warning("Sleeping for " + str(delay / 60) + " minutes")
#             time.sleep(delay)
#             numCycles -= 1
#             if numCycles < 1:  # Sanity check against infinite loop
#                 stillHaveDrops = 0
#
#             logging.warning(
#                 "Checking to see if " + getAppName(appID) + " has remaining card drops")
#             rBadge = requests.get(
#                 myProfileURL + "/gamecards/" + str(appID) + "/", cookies=cookies)
#             indBadgeData = bs4.BeautifulSoup(rBadge.text)
#             badgeLeftString = indBadgeData.find_all(
#                 "span", {"class": "progress_info_bold"})[0].contents[0]
#             if "No card drops" in badgeLeftString:
#                 logging.warning("No card drops remaining")
#                 stillHaveDrops = 0
#             else:
#                 dropCountInt, junk = badgeLeftString.split(" ", 1)
#                 dropCountInt = int(dropCountInt)
#                 delay = dropDelay(dropCountInt)
#                 logging.warning(
#                     getAppName(appID) + " has " + str(dropCountInt) + " card drops remaining")
#                 if sys.platform.startswith('win32'):
#                     ctypes.windll.kernel32.SetConsoleTitleA(
#                         "Idle Master - Idling " + getPlainAppName(appID) + " [" + str(dropCountInt) + " remaining]")
#         except:
#             if maxFail > 0:
#                 logging.warning(
#                     "Error checking if drops are done, number of tries remaining: " + str(maxFail))
#                 maxFail -= 1
#             else:
#                 # Suspend operations until Steam can be reached.
#                 chillOut(appID)
#                 maxFail += 1
#                 break
#
#     idleClose(appID)
#     logging.warning(
#         Fore.GREEN + "Successfully completed idling cards for " + getAppName(appID) + Fore.RESET)
#
# logging.warning(
#     Fore.GREEN + "Successfully completed idling process" + Fore.RESET)
# input("Press Enter to continue...")
