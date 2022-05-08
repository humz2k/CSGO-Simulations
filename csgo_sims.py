import pandas as pd
from random import choice,randint,uniform

class Team:
    def __init__(self,name,stats):
        self.name = name
        self.stats = stats
        self.wins = 0
        self.losses = 0
        self.points = 0
        self.seed = int(self.stats["seed"])
        self.prior_opponents = []

    def reset(self):
        self.wins = 0
        self.losses = 0
        self.points = 0
        self.prior_opponents = []

    def buch(self):
        score = 0
        for t in self.prior_opponents:
            score += t.wins
            score -= t.losses
        return score

class Match:
    def __init__(self,team1,team2):
        self.team1,self.team2 = team1,team2
        self.winner = None
        self.loser = None
        self.gamestats = None

    def play(self,play_func):
        self.winner,self.gamestats = play_func(self.team1,self.team2)
        if self.winner.name == self.team1.name:
            self.loser = self.team2
        else:
            self.loser = self.team1
        self.winner.wins += 1
        self.loser.losses += 1
        self.winner.points += self.gamestats.score[0]
        self.loser.points += self.gamestats.score[1]
        self.winner.prior_opponents.append(self.loser)
        self.loser.prior_opponents.append(self.winner)

    def __str__(self):
        if self.winner != None:
            #return self.winner.name + "/" + self.loser.name + " " + str(self.gamestats.score[0]) + "-" + str(self.gamestats.score[1]) + " with RD = " + str(self.gamestats.rd)
            return "{:<16}({:<3}) beats {:<16} ({:<3}), {:<3} (+{})".format(self.winner.name,(str(self.winner.wins) + "-" + str(self.winner.losses)),self.loser.name,(str(self.loser.wins) + "-" + str(self.loser.losses)),(str(self.gamestats.score[0]) + "-" + str(self.gamestats.score[1])),str(self.gamestats.rd))
        return "{:<16}({:<3})  vs   {:<16} ({:<3})".format(self.team1.name,(str(self.team1.wins) + "-" + str(self.team1.losses)),self.team2.name,(str(self.team2.wins) + "-" + str(self.team2.losses)))


class Table:
    def __init__(self,round1,teams):
        self.round1 = round1
        self.teams = teams
        self.reset()

    def reset(self):
        self.rounds = [[Match(teams[i[0]],teams[i[1]]) for i in self.round1]]
        self.elims = []
        self.promotes = []
        for t in self.teams.keys():
            self.teams[t].reset()

    def do_sims(self,play_func,nsims=100,nstages=5,verbose=True):
        data = {}
        for i in self.teams.keys():
            data[i] = {"promotion%":0,"(3-0)%":0,"(3-1)%":0,"(3-2)%":0,"(2-3)%":0,"(1-3)%":0,"(0-3)%":0}
        for sim in range(nsims):
            results = self.play(play_func,verbose=False,nstages=nstages)
            for i in results["promoted"]:
                data[i]["promotion%"] += 1
            possibilities = [(3,0),(3,1),(3,2),(2,3),(1,3),(0,3)]
            for key in possibilities:
                strkey = "(" + str(key[0]) + "-" + str(key[1]) + ")%"
                for i in results[key]:
                    data[i][strkey] += 1
        for i in self.teams.keys():
            for j in data[i].keys():
                data[i][j] = data[i][j]/nsims
        if verbose:
            print("{:<16} {:>10} {:>6} {:>6} {:>6} {:>6} {:>6} {:>6}".format("Team","Promotion%","(3-0)%","(3-1)%","(3-2)%","(2-3)%","(1-3)%","(0-3)%"))
            print("=====================================================================")
            team_list = list(self.teams.keys())
            team_list.sort(key=lambda x:data[x]["promotion%"],reverse=True)
            for i in team_list:
                print("{:<16} {:>10} {:>6} {:>6} {:>6} {:>6} {:>6} {:>6}".format(i,*[str(round((data[i][key]*100)))+"%" for key in data[i].keys()]))
                #print("{:<16} {:>4}".format(i,str(round((data[i]["promotion%"]*100)))+"%"))
        return data

    def play(self,play_func,verbose=True,nstages=5):
        self.reset()
        for i in range(nstages):
            self.play_round(i,play_func)
            if verbose:
                self.print_round(i)
            self.prop_round(i)

        if verbose:
            print("============================Result===========================")
            print("Eliminated")
            print("----------")
            for i in self.elims:
                print(i.name)
            print("\nPromoted")
            print("----------")
            for i in self.promotes:
                print(i.name)
        out = {"eliminated":[i.name for i in self.elims],"promoted":[i.name for i in self.promotes]}

        for i in self.teams.keys():
            record = (self.teams[i].wins,self.teams[i].losses)
            if record in out:
                out[record].append(i)
            else:
                out[record] = [i]

        return out

    def print_round(self,round):
        print("============================Round"+str(round)+"===========================")
        for game in self.rounds[round]:
            print(game)

    def play_round(self,round,play_func):
        for game in self.rounds[round]:
            game.play(play_func)

    def prop_round(self,round):
        sections = {}
        for game in self.rounds[round]:
            if game.winner.wins > 2:
                self.promotes.append(game.winner)
            else:
                winner_score = (game.winner.wins,game.winner.losses)
                if winner_score in sections:
                    sections[winner_score].append(game.winner)
                else:
                    sections[winner_score] = [game.winner]

            if game.loser.losses > 2:
                self.elims.append(game.loser)
            else:
                loser_score = (game.loser.wins,game.loser.losses)
                if loser_score in sections:
                    sections[loser_score].append(game.loser)
                else:
                    sections[loser_score] = [game.loser]
        games = []
        for s in sections.keys():
            ts = sections[s]
            if round == 0 or round == 1:
                ts.sort(key=lambda x:x.seed)
            else:
                ts.sort(key=lambda x:x.seed)
                ts.sort(key=lambda x:x.buch(),reverse=True)
            games += [Match(*game) for game in list(zip(ts[:len(ts)//2],ts[len(ts)//2:][::-1]))]
        self.rounds.append(games)

class GameStats:
    def __init__(self,rd,score):
        self.score,self.rd = score,rd

def random(team1,team2):
    bo3 = False
    if team1.wins == 2 or team1.losses == 2 or team2.wins == 2 or team2.losses == 2:
        bo3 = True

    winner_score = 1
    loser_score = 0
    round_diff = randint(2,16)
    if bo3:
        winner_score = 2
        loser_score = randint(0,1)
        round_diff = randint(0,(winner_score+loser_score)*16)

    return choice([team1,team2]),GameStats(round_diff,(winner_score,loser_score))

def ilyas_rating_only(team1,team2):
    bo3 = False
    if team1.wins == 2 or team1.losses == 2 or team2.wins == 2 or team2.losses == 2:
        bo3 = True

    total_rating = team1.stats["ilyasrating"] + team2.stats["ilyasrating"]
    team1chance = team1.stats["ilyasrating"]/total_rating
    team2chance = team2.stats["ilyasrating"]/total_rating

    ngames = 1
    if bo3:
        ngames = 2

    team1score = 0
    team2score = 0
    team1totalgamescore = 0
    team2totalgamescore = 0
    while team1score != ngames and team2score != ngames:
        team1gamescore = 0
        team2gamescore = 0
        while team1gamescore != 16 and team2gamescore != 16:
            if uniform(0,1) > team1chance:
                team2gamescore += 1
            else:
                team1gamescore += 1
        if team1gamescore == 15:
            team1gamescore -= 1
        if team2gamescore == 15:
            team2gamescore -= 1
        team1totalgamescore += team1gamescore
        team2totalgamescore += team2gamescore
        if team1gamescore > team2gamescore:
            team1score += 1
        else:
            team2score += 1
    winner = team2
    loser = team1
    winner_score = team2score
    loser_score = team1score
    rd = team2totalgamescore-team1totalgamescore
    if team1score > team2score:
        winner = team1
        loser = team2
        winner_score = team1score
        loser_score = team2score
        rd = team1totalgamescore-team2totalgamescore

    return winner,GameStats(rd,(winner_score,loser_score))

def hltv_rating_only(team1,team2):
    bo3 = False
    if team1.wins == 2 or team1.losses == 2 or team2.wins == 2 or team2.losses == 2:
        bo3 = True

    total_rating = team1.stats["hltv"] + team2.stats["hltv"]
    team1chance = team1.stats["hltv"]/total_rating
    team2chance = team2.stats["hltv"]/total_rating

    ngames = 1
    if bo3:
        ngames = 2

    team1score = 0
    team2score = 0
    team1totalgamescore = 0
    team2totalgamescore = 0
    while team1score != ngames and team2score != ngames:
        team1gamescore = 0
        team2gamescore = 0
        while team1gamescore != 16 and team2gamescore != 16:
            if uniform(0,1) > team1chance:
                team2gamescore += 1
            else:
                team1gamescore += 1
        if team1gamescore == 15:
            team1gamescore -= 1
        if team2gamescore == 15:
            team2gamescore -= 1
        team1totalgamescore += team1gamescore
        team2totalgamescore += team2gamescore
        if team1gamescore > team2gamescore:
            team1score += 1
        else:
            team2score += 1
    winner = team2
    loser = team1
    winner_score = team2score
    loser_score = team1score
    rd = team2totalgamescore-team1totalgamescore
    if team1score > team2score:
        winner = team1
        loser = team2
        winner_score = team1score
        loser_score = team2score
        rd = team1totalgamescore-team2totalgamescore

    return winner,GameStats(rd,(winner_score,loser_score))

team_stats = pd.read_csv("team-stats.csv")
team_stats = team_stats.set_index("name")
teams = {}
for team_name in team_stats.index.values:
    teams[team_name] = Team(team_name,team_stats.loc[team_name].to_dict())

opening_games = pd.read_csv("round1.csv")
team1s = opening_games['team1'].tolist()
team2s = opening_games['team2'].tolist()
round1matches = list(zip(team1s,team2s))

table = Table(round1matches, teams)
