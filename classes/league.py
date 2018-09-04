import requests
from bs4 import BeautifulSoup
import time
import datetime


class espn_urls:
    HOMEPAGE = "http://games.espn.com/ffl/leagueoffice?leagueId={0}&seasonId={1}"
    STANDINGS = "http://games.espn.com/ffl/standings?leagueId={0}&seasonId={1}"
    FINAL_STANDINGS = "http://games.espn.com/ffl/tools/finalstandings?leagueId={0}&seasonId={1}"
    DRAFT = "http://games.espn.com/ffl/tools/draftrecap?leagueId={0}&seasonId={1}"
    MEMBERS = "http://games.espn.com/ffl/leaguesetup/ownerinfo?leagueId={0}&seasonId={1}"
    TEAM = "http://games.espn.com/ffl/clubhouse?leagueId={0}&teamId={1}&seasonId={2}"
    SETTINGS = "http://games.espn.com/ffl/leaguesetup/settings?leagueId={0}&seasonId={1}"

class League:
    
    def __init__(self, league_id, year):
        # __init__
        self.league_id = league_id
        self.year = year
        self.exists = None
        self.draft_type = None
        self.private = None
        self.draft_soup = None
        
        # scrape_settings(self)
        self.league_name = None
        self.num_teams = None
        self.scoring_type = None
        self.roster_size = None
        self.num_starters = None
        self.num_bench = None
        self.roster_breakdown = None
        self.ppr_pts = None
        self.keepers = None
        
        # scrape_teams(self)
        self.team_ids = None
        self.team_names = None
        self.team_pf = None
        self.team_pa = None
        self.team_records = None
        
        # parse_draft(self)
        self.draft_picks = None
        self.drafted_players = None

        # Now scrape for other league variables
        r = requests.get(espn_urls.DRAFT.format(league_id, year))
        soup = BeautifulSoup(r.content, "html.parser")
        header = soup.find_all('h1')[1].text

        if (header == "Draft Recap"):
            self.exists = True
            self.draft_type = 'draft'
            self.private = False
        elif (header == "Auction Recap"):
            self.exists = True
            self.draft_type = 'auction'
            self.private = False  
        elif (header == "Log In"):
            self.exists = True
            self.draft_type = None
            self.private = True
        elif (header == "We're Sorry"):
            self.exists = False
            self.draft_type = None
            self.private = None
        
        self.draft_soup = soup

    
    def scrape_settings(self):
        if not self.scrapeable():
            print("League not scrapeable... Please try another league")
            return
        
        r = requests.get(espn_urls.SETTINGS.format(self.league_id, self.year))
        soup = BeautifulSoup(r.content,"html.parser")
        tables = soup.find_all('table')

        # League settings
        generalSettings_table = tables[1]
        self.league_name = soup.find(text = "League Name").__dict__['next_element'].text.replace("'","").replace(".","")
        self.num_teams = int(soup.find(text = "Number of Teams").__dict__['next_element'].text)
        self.scoring_type = (soup.find(text = "Scoring Type").__dict__['next_element'].text).lower().replace(' ','_')

        # Basic roster information
        rosterSettings_table = tables[2]
        self.roster_size = int(rosterSettings_table.findAll('p')[0].text.split(': ')[1])
        self.num_starters = int(rosterSettings_table.findAll('p')[1].text.split(': ')[1])
        self.num_bench = int(rosterSettings_table.findAll('p')[2].text.split(': ')[1].split(' ')[0])

        # Breakdown of roster positions
        self.roster_breakdown = {}
        roster_table = rosterSettings_table.find('table')
        for position_row in roster_table.find_all('tr')[1:]:
            pos_abrv = position_row.find_all('td')[0].text.split(' (')[1][:-1].replace('/','_').lower()
            pos_starters = position_row.find_all('td')[1].text
            self.roster_breakdown[pos_abrv] = pos_starters

        # Points per reception (PPR)
        ppr_tag = tables[4].find(text='Each reception (REC)')
        if ppr_tag == None:
            self.ppr_pts = 0
        else:
            self.ppr_pts = float(ppr_tag.__dict__['next_element'].text)
            
        # Keepers
        keeper_tag = soup.find(text= str(self.year) + " Keepers Per Team")
        keeper_text = keeper_tag.__dict__['next_element'].text
        if keeper_text == 'None':
            self.keepers = 0
        else:
            self.keepers = int(keeper_text)
        
        return

    def scrape_teams(self):
        if not self.scrapeable():
            print("League not scrapeable... Please try another league")
            return
        elif datetime.datetime.now().year > int(self.year):
            r = requests.get(espn_urls.FINAL_STANDINGS.format(self.league_id, self.year))
            soup = BeautifulSoup(r.content, "html.parser")
            table = soup.find_all('table')[1]

            self.team_names = {}
            self.team_pf = {}
            self.team_pa = {}
            self.team_records = {}

            for team_row in table.find_all('tr')[2:]:
                team_cols = team_row.find_all('td')
                team_nameEntry = team_cols[1]
                team_name = team_nameEntry.text.replace("'",'')
                team_url = team_nameEntry.find('a').get('href')
                team_id = int(team_url.split('teamId=')[1].split('&')[0])
                self.team_names[team_id] = team_name
                self.team_pf[team_id] = float(team_cols[5].text)
                self.team_pa[team_id] = float(team_cols[6].text)

                record = team_cols[4].text.split('-')
                if len(record) == 2:
                    record.append('0')
                record = list(map(int,record))        
                self.team_records[team_id] = record

                self.team_ids = list(self.team_names.keys())

            return

        elif datetime.datetime.now().year == int(self.year): 
            r = requests.get(espn_urls.STANDINGS.format(self.league_id, self.year))
            soup = BeautifulSoup(r.content, "html.parser")

            self.team_names = {}
            self.team_pf = {}
            self.team_pa = {}
            self.team_records = {}

            num_divs = len(soup.find('div', class_='games-pageheader').next_sibling.find_all('table'))
            for div in range(0,num_divs):
                team_rows = soup.find('table', {'id':'xstandTbl_div'+str(div)}).find_all('tr')[2:]
                for team_row in team_rows:
                    team_id = int(team_row.find('a').get('href').split('teamId=')[1].split('&')[0])
                    self.team_names[team_id] = team_row.find('a').text.replace("'",'')
                    self.team_pf[team_id] = float(team_row.find('td',class_='sortablePF').text)
                    self.team_pa[team_id] = float(team_row.find('td',class_='sortablePA').text)
                    home_rec = team_row.find('td', class_='sortableHOME').text.split('-')
                    away_rec = team_row.find('td', class_='sortableAWAY').text.split('-')
                    self.team_records[team_id] = [int(home_rec[x])+int(away_rec[x]) for x in range(0,3)]

            self.team_ids = list(self.team_names.keys())
            
            return
        
        return


    def parse_draft(self):
        if self.draft_soup == None:
            print('draft_soup does not exist')
            return
        
        soup = self.draft_soup
        round_tables = soup.find_all('table')[2:]
        
        self.draft_picks = []
        self.drafted_players = []
        for round_table in round_tables:
            pick_rows = round_table.find_all('tr')
            round_number = int(pick_rows[0].text.split(' ')[1])

            for pick_row in pick_rows[1:]:
                pick_cols = pick_row.find_all('td')
                pick_number = int(pick_cols[0].text)
                if pick_cols[2].find('a') == None:
                    self.draft_type = 'auction'
                    return
                owner_id = int(pick_cols[2].find('a').get('href').split('teamId=')[1].split('&')[0])
                
                player_str = pick_cols[1].text
                if player_str == '-':
                    player_id = 'NULL'
                    keeper = 'NULL'
                else:    
                    player_id = int(pick_cols[1].find('a').get('playerid'))
                    if pick_cols[1].find('span', attrs={'title':'Keeper Selection'}) == None:
                        keeper = 'FALSE'
                    else:
                        keeper = 'TRUE'

                    if 'D/ST' in player_str:
                        player_name = player_str.split(' ')[0] + ' d_st'
                        player_team = team_abbreviations[player_str.split(' ')[0]]
                        player_pos = 'd_st'
                    elif 'Coach' in player_str:
                        player_name = player_str
                        player_team = team_abbreviations[player_str.split(' ')[0]]
                        player_pos = 'coach'
                    elif 'TQB' in player_str:
                        self.draft_type = 'TQB'
                        return
                    else:
                        player_name = player_str.split(',')[0].replace("'","").replace(".","")
                        player_team = player_str.split(',')[1].split(u'\xa0')[0].lower().replace(' ','')
                        player_pos = player_str.split(',')[1].split(u'\xa0')[1].lower()
                        
                    self.drafted_players.append([player_id, player_name, player_pos, player_team])    

                self.draft_picks.append([owner_id, pick_number, round_number, player_id, keeper])

        return
    
    
    def scrape_all(self, parse = True):
        if random.random() > 0.5:
            self.scrape_settings()
            self.scrape_teams()
        else:
            self.scrape_teams()
            self.scrape_settings()

        if parse:
            self.parse_draft()
        
        return
    
    
    def scrapeable(self):
        if self.exists and not self.private and self.draft_type=='draft':
            return True
        else:
            return False
    
    
    def display(self):
        return vars(self)



team_abbreviations = {
    'Cardinals': 'ari',
    'Falcons': 'atl',
    'Ravens': 'bal',
    'Bills': 'buf',
    'Panthers': 'car',
    'Bears': 'chi',
    'Bengals': 'cin',
    'Browns': 'cle',
    'Cowboys': 'dal',
    'Broncos': 'den',
    'Lions': 'det',
    'Packers': 'gb',
    'Texans': 'hou',
    'Colts': 'ind',
    'Jaguars': 'jac',
    'Chiefs': 'kc',
    'Rams': 'lar',
    'Dolphins': 'mia',
    'Vikings': 'min',
    'Patriots': 'ne',
    'Saints': 'no',
    'Giants': 'nyg',
    'Jets': 'nyj',
    'Raiders': 'oak',
    'Eagles': 'phi',
    'Steelers': 'pit',
    'Seahawks': 'sea',
    '49ers': 'sf',
    'Buccaneers': 'tb',
    'Titans': 'ten',
    'Redskins': 'was',
    'Chargers': 'lac'
}
