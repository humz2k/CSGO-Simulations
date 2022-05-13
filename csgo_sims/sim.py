import pandas as pd
from random import choice,randint,uniform
from datetime import datetime
from .elo_system import Rating,rate_1vs1,quality_1vs1

def isbo3(team1,team2):
    if team1.wins == 2 or team1.losses == 2 or team2.wins == 2 or team2.losses == 2:
        return True
    return False

class Data:
    def __init__(self,filename):
        self.df = pd.read_csv(filename)
        self.load()

    def __str__(self):
        return str(self.df)

    def load(self):
        pass

class Team:
    def __init__(self,name,stats,seed=None):
        self.name = name
        self.stats = stats
        self.wins = 0
        self.losses = 0
        self.points = 0
        self.seed = seed
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

    def __str__(self):
        out = str(self.name)
        if self.seed != None:
            out += "\n    -seed:" + str(self.seed)
        for key in self.stats.keys():
            out += "\n    -{:<18} {:>10}".format(str(key)+":",self.stats[key])
        if self.wins != 0 and self.losses != 0:
            out += "\n    -losses: " + str(self.losses)
            out += "\n    -wins: " + str(self.wins)
        return out

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
            return "{:<18}({:<3}) beats {:<18} ({:<3}), {:<3} (+{})".format(self.winner.name,(str(self.winner.wins) + "-" + str(self.winner.losses)),self.loser.name,(str(self.loser.wins) + "-" + str(self.loser.losses)),(str(self.gamestats.score[0]) + "-" + str(self.gamestats.score[1])),str(self.gamestats.rd))
        return "{:<18}({:<3})  vs   {:<18} ({:<3})".format(self.team1.name,(str(self.team1.wins) + "-" + str(self.team1.losses)),self.team2.name,(str(self.team2.wins) + "-" + str(self.team2.losses)))

class Matches:
    def __init__(self,filename,types=None):
        with open(filename,"r") as f:
            raw = [i.split(",") for i in f.read().splitlines()]
        headers = raw[0]
        raw = raw[1:]
        matches = []
        for game in raw:
            temp = {}
            for header,data in zip(headers,game):
                temp[header] = data
                if types != None:
                    if types[header] != "date":
                        temp[header] = types[header](temp[header])
                    else:
                        temp[header] = datetime.utcfromtimestamp(float(temp[header]))
            if not temp in matches:
                matches.append(temp)
        self.df = pd.DataFrame.from_dict(matches)
    
    def __getitem__(self,i):
        return self.df.iloc[i]
    
    def find(self,team,winheader="winner",loseheader="loser"):
        return pd.concat([self.df.loc[self.df[winheader] == team],self.df.loc[self.df[loseheader] == team]])

    def get_elo(self,winnerindex,loserindex,winnerscore,loserscore):
        sorted_df = self.df.sort_values(by="date")
        out = {}
        for i in range(len(sorted_df)):
            temp = sorted_df.iloc[i]
            if not temp[winnerindex] in out:
                out[temp[winnerindex]] = Rating(1000)
            if not temp[loserindex] in out:
                out[temp[loserindex]] = Rating(1000)
            if temp[winnerscore] > 5:
                out[temp[winnerindex]],out[temp[loserindex]] = rate_1vs1(out[temp[winnerindex]],out[temp[loserindex]])
            else:
                for i in range(temp[winnerscore]):
                    out[temp[winnerindex]],out[temp[loserindex]] = rate_1vs1(out[temp[winnerindex]],out[temp[loserindex]])
                for i in range(temp[loserscore]):
                    out[temp[loserindex]],out[temp[winnerindex]] = rate_1vs1(out[temp[loserindex]],out[temp[winnerindex]])
        return out

class TeamData(Data):
    def load(self):
        self.teams = {}
        self.df = self.df.set_index("name")
        for name in self.df.index:
            self.teams[name] = Team(name,self.df.loc[name].to_dict())

    def get_elo(self,matches,winnerindex,loserindex,winnerscore,loserscore):
        elos = matches.get_elo(winnerindex,loserindex,winnerscore,loserscore)
        for team in self.teams.keys():
            self.teams[team].stats["elo"] = elos[team]

    def __getitem__(self, i):
        if i not in self.teams:
            return False
        return self.teams[i]

class SeedData(Data):
    def load(self):
        self.dict = {}
        self.df = self.df.set_index("name")
        self.team_names = []
        for name in self.df.index:
            self.team_names.append(name)
            self.dict[name] = self.df.loc[name].to_numpy().flatten()[0]

    def __getitem__(self, i):
        return self.dict[i]

class GameStats:
    def __init__(self,rd,score):
        self.score,self.rd = score,rd

class Table:
    def __init__(self,team_data,seeds):
        self.teams = {}
        for name in seeds.team_names:
            self.teams[name] = team_data[name]
            self.teams[name].seed = seeds[name]
        names_sorted = sorted(list(self.teams.keys()),key=lambda x : self.teams[x].seed)
        self.round1 = list(zip(names_sorted[:len(names_sorted)//2],names_sorted[len(names_sorted)//2:][::-1]))

        self.reset()

    def reset(self):
        self.rounds = [[Match(self.teams[i[0]],self.teams[i[1]]) for i in self.round1]]
        self.elims = []
        self.promotes = []
        for t in self.teams.keys():
            self.teams[t].reset()

    def do_sims(self,play_func,nsims=100,nstages=5,verbose=True,file=None):
        data = {}
        tree = {}
        for i in self.teams.keys():
            data[i] = {"promotion%":0,"(3-0)%":0,"(3-1)%":0,"(3-2)%":0,"(2-3)%":0,"(1-3)%":0,"(0-3)%":0}
        for sim in range(nsims):
            results,branch = self.play(play_func,verbose=False,nstages=nstages)
            temp_tree = tree
            for line in branch:
                old = temp_tree
                if not line in temp_tree:
                    temp_tree[line] = {"count":1,"next":{}}
                else:
                    temp_tree[line]["count"] += 1
                temp_tree = temp_tree[line]["next"]
            old[line] = results

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
            print("{:<18} {:>10} {:>6} {:>6} {:>6} {:>6} {:>6} {:>6}".format("Team","Promotion%","(3-0)%","(3-1)%","(3-2)%","(2-3)%","(1-3)%","(0-3)%"))
            print("=======================================================================")
            team_list = list(self.teams.keys())
            team_list.sort(key=lambda x:data[x]["promotion%"],reverse=True)
            for i in team_list:
                print("{:<18} {:>10} {:>6} {:>6} {:>6} {:>6} {:>6} {:>6}".format(i,*[str(round((data[i][key]*100)))+"%" for key in data[i].keys()]))

        if file != None:
            with open(file,"w") as f:
                f.write("{:<18} {:>10} {:>6} {:>6} {:>6} {:>6} {:>6} {:>6}".format("Team","Promotion%","(3-0)%","(3-1)%","(3-2)%","(2-3)%","(1-3)%","(0-3)%\n"))
                f.write("=======================================================================\n")
                team_list = list(self.teams.keys())
                team_list.sort(key=lambda x:data[x]["promotion%"],reverse=True)
                for i in team_list:
                    f.write("{:<18} {:>10} {:>6} {:>6} {:>6} {:>6} {:>6} {:>6}\n".format(i,*[str(round((data[i][key]*100)))+"%" for key in data[i].keys()]))

        return data,tree

    def play(self,play_func,verbose=True,nstages=5):
        self.reset()
        for i in range(nstages):
            self.play_round(i,play_func)
            if verbose:
                self.print_round(i)
            self.prop_round(i)

        if verbose:
            print("==============================Result===========================")
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
        branch = []
        for stage in self.rounds[:-1]:
            matchups = []
            for matchup in stage:
                matchups.append((matchup.winner.name,matchup.loser.name))
            branch.append(tuple(matchups))
        branch = tuple(branch)
        return out,branch

    def print_round(self,round):
        print("==========================Round"+str(round)+"===========================")
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
            if round == 3:
                temp1 = ts[:len(ts)//2] + ts[len(ts)//2:]
                temp2 = ts[len(ts)//2:][::-1] + ts[:len(ts)//2][::-1]
                while len(temp1) != 0:
                    current = temp1[0]
                    for idx in range(len(temp2)):
                        if temp2[idx].name != current.name:
                            if not temp2[idx].name in [i.name for i in current.prior_opponents]:
                                games.append(Match(current,temp2[idx]))
                                temp2.pop(idx)
                                break
                    temp1.pop(0)
                    for idx in range(len(temp2)):
                        if temp2[idx].name == current.name:
                            temp2.pop(idx)
                            break
                #games += [Match(*game) for game in list(zip(ts[:len(ts)//2],ts[len(ts)//2:][::-1]))]
            else:
                games += [Match(*game) for game in list(zip(ts[:len(ts)//2],ts[len(ts)//2:][::-1]))]
        self.rounds.append(games)

class PlayFunc(object):
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
