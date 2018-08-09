import nba_py.player
import nba_py.team
import nba_py.game
import nba_py.league
import nba_py.draftcombine
import dateutil.parser
import datetime
import sys
sys.path.append('/Users/chris/Desktop/NBA Injury Data/shoecontracts')
import shoecontracts
import shoecontracts.utils
import logging
from pprint import pprint
from lxml import html
import requests
import openpyxl
logger = logging.getLogger(__name__)

def fetch_players(season=None, only_current=1):
    logger.info('Downloading player data...')
    if not season:
        season = nba.utils.valid_season(nba.CURRENT_SEASON)# if the user does not specify a season, download all seasons
        only_current = 0
    draft_combine = {}# TODO: handle only_current season...
    for p in nba_py.draftcombine.DrillResults(season=season.raw).overall():
        player = {
            'bench_press': p['BENCH_PRESS'],
            'three_quarter_sprint': p['THREE_QUARTER_SPRINT'],
            'lane_agility_time': p['LANE_AGILITY_TIME'],
            'modified_lane_agility_time': p['MODIFIED_LANE_AGILITY_TIME'],
            'standing_vertical_leap': p['STANDING_VERTICAL_LEAP']
        }
        draft_combine[p['PLAYER_NAME']] = player# use dictionary to ensure uniqueness
    players = {}
    for p in nba_py.player.PlayerList(season=season.raw,
                                      only_current=only_current).info():
        if p['GAMES_PLAYED_FLAG'] is 'N':
            continue
        player = nba_py.player.PlayerSummary(p['PERSON_ID']).info()[0]
        if p['ROSTERSTATUS'] is 'Inactive':
            continue
        player_id = player['PERSON_ID']
        first_name = player['FIRST_NAME']
        last_name = player['LAST_NAME']
        player = {
            'player_id': player_id,
            'first_name': first_name,
            'last_name': last_name,
            'birthdate': dateutil.parser.parse(player['BIRTHDATE']).date(),
            'height': nba.utils.height_in_inches(player['HEIGHT'] or None),
            'weight': player['WEIGHT'] or None,
            'from_year': nba.utils.season_start(player['FROM_YEAR']),
            'to_year': nba.utils.season_end(player['TO_YEAR']),
            'position': player['POSITION'] or None,
        }
        try:# TODO: is there any better way of id than first and last name?
            player.update(draft_combine[p['DISPLAY_FIRST_LAST']])
        except:
            pass
        players[player_id] = player
    return players.values()

def fetch_teams():
    logger.info('Downloading team data...') # use dictionary to ensure uniqueness
    teams = {}
    for t in nba_py.team.TeamList().info():
        try:
            team = nba_py.team.TeamDetails(t['TEAM_ID']).background()[0]
            del(team['YEARFOUNDED'])
        except IndexError:#  historical team
            continue
        team['MIN_YEAR'] = datetime.datetime(int(t['MIN_YEAR']), 1, 1)
        team['MAX_YEAR'] = datetime.datetime(int(t['MAX_YEAR']), 1, 1)
        team = dict((k.lower(), v) for k, v in team.items())
        teams[team['team_id']] = team
    return teams.valvues()

def fetch_shoe_contracts(season=None):
    if not season:
        season = shoecontracts.utils.valid_season(shoecontracts.CURRENT_SEASON)
    teams = ['hawks','celtics','nets','hornets','bulls','cavaliers','mavericks','nuggets',
         'pistons','warriors','rockets','pacers','clippers','heat','bucks','timberwolves','pelicans',
         'knicks','thunder','magic','sixers','suns','blazer','kings','spurs','raptors','jazz']
    logger.info('Downloading shoe contract data...')
    page = requests.get('http://nbashoesdb.com/en/team/pacers')
    tree=html.fromstring(page.content)
    e = tree.xpath('/html/body/div[2]/section/div[5]/div/div[2]/div/table/tbody/tr/td[2]/a/text()')
    f = [i.split('\n\t\t\t\t\t\t\t\t\t\t\t')[1] for i in e]
    pacerplayers = [i.split('\t\t\t\t\t\t\t\t\t\t')[0] for i in f]
    ab = range(1,16,1)
    del ab[10]
    pacershoes = []
    for i in ab:
        ac = tree.xpath('/html/body/div[2]/section/div[5]/div/div[2]/div/table/tbody/tr[%s]/td[7]/a/text()' % i) 
        ad = [k.split('\n\t\t\t\t\t\t\t\t\t\t')[1] for k in ac]
        ae = [k.split('\t\t\t\t\t\t\t\t\t\t')[0] for k in ad]
        pacershoes.append(ae)
    pacershoes.insert(10,'Air Jordan 10 Retro "Ovo"')
    pacercontracts = {}
    for l in range(0,len(pacerplayers)):
        pacercontracts[l] = {
            'name':pacerplayers[l],
            'shoe':pacershoes[l],
            'team':'pacers',
            'season':season.raw
            }
    teams.remove('pacers')
    teamcontract = {}
    for i in range(0,len(teams)):
        site = 'http://nbashoesdb.com/en/team/%s' % teams[i]
        page = requests.get(site)
        tree = html.fromstring(page.content)
        a = tree.xpath('/html/body/div[2]/section/div[5]/div/div[2]/div/table/tbody/tr/td[2]/a/text()')
        b = [k.split('\n\t\t\t\t\t\t\t\t\t\t\t')[1] for k in a]
        names = [k.split('\t\t\t\t\t\t\t\t\t\t')[0] for k in b]
        c = tree.xpath('/html/body/div[2]/section/div[5]/div/div[2]/div/table/tbody/tr/td[7]/a/text()')
        d = [k.split('\n\t\t\t\t\t\t\t\t\t\t')[1] for k in c]
        shoes = [k.split('\t\t\t\t\t\t\t\t\t\t')[0] for k in d]
        playercontract = {}
        for j in range(0,len(names)):
            playercontract[j] = {
                'name':names[j],
                'shoe':shoes[j],
                'team':teams[i],
                'season':season.raw
                }
        teamcontract[i]=playercontract
    teamcontract["pacers"] = pacercontracts
    return teamcontract.values()

