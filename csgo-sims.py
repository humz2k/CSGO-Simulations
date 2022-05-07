import pandas as pd
import numpy as np
from random import choice

class Team:
    def __init__(self,name,stats):
        self.name = name
        self.stats = stats
        self.wins = 0
        self.losses = 0
        self.points = 0
        self.seed = int(self.stats["seed"])
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

    def play(self,play_func,verbose=True,nstages=5):
        self.reset()
        for i in range(nstages):
            self.play_round(i,play_func)
            if verbose:
                self.print_round(i)
            if i != 4:
                self.prop_round(i)
        if verbose:
            print("============================Result===========================")
            print("Eliminated")
            print("----------")
            for i in self.elims:
                print(i.name)
            print("Promoted")
            print("----------")
            for i in self.promotes:
                print(i.name)
        return {"eliminated":[i.name for i in self.elims],"promoted":[i.name for i in self.promotes]}

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

team_stats = pd.read_csv("team-stats.csv")
team_stats = team_stats.set_index("name")
teams = {}
for team_name in team_stats.index.values:
    teams[team_name] = Team(team_name,team_stats.loc[team_name].to_dict())

opening_games = pd.read_csv("round1.csv")
team1s = opening_games['team1'].tolist()
team2s = opening_games['team2'].tolist()
round1matches = list(zip(team1s,team2s))

def hltvonly(team1,team2):
    total_score = 16
    bo3 = False
    if team1.wins == 2 or team1.losses == 2 or team2.wins == 2 or team2.losses == 2:
        bo3 = True

    diff = team1.stats["hltv"] - team2.stats["hltv"]

    winner_score = 1
    loser_score = 0

    if diff > 0:
        if bo3:
            winner_score = round((3/(team1.stats["hltv"] + team2.stats["hltv"])) * team1.stats["hltv"])
            if winner_score == 1:
                winner_score = 2
            loser_score = 3 - winner_score
        other_score = round((total_score/team1.stats["hltv"]) * team2.stats["hltv"])
        rd = total_score - other_score
        if rd == 0 or rd == 1:
            rd = 2
        return team1,GameStats(rd,(winner_score,loser_score))
    if diff < 0:
        if bo3:
            winner_score = round((3/(team2.stats["hltv"] + team1.stats["hltv"])) * team2.stats["hltv"])
            if winner_score == 1:
                winner_score = 2
            loser_score = 3 - winner_score
        other_score = round((total_score/team2.stats["hltv"]) * team1.stats["hltv"])
        rd = total_score - other_score
        if rd == 0 or rd == 1:
            rd = 2
        return team2,GameStats(rd,(winner_score,loser_score))
    else:
        if bo3:
            winner_score = 2
            loser_score = 1
        return choice([team1,team2]),GameStats(2,(1,0))

table = Table(round1matches, teams)

results = table.play(hltvonly)
# %% codecell
