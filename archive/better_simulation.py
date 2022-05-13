# %% markdown
## Simulating the Challenger Stage of PGL Antwerp
# %% codecell
import csgo_sims #load simulation
from random import choice,randint,uniform
csgo_sims.table.reset()
teams = csgo_sims.teams #alias teams
# %% markdown
#### Load curated list of tier 1/tier 2 teams
# %% codecell
tiers = {}
with open("tiers.txt","r") as f:
    for rawtier in f.read().split("#")[1:]:
        name = rawtier.split("\n")[0].lower()
        teams = rawtier.split("\n")[1:-1]
        tiers[name] = teams
# %% markdown
#### Function to find recent matches
# %% codecell
def find_recents(team):
    out = []
    for match in csgo_sims.recentmatches:
        if match["winner"] == team.name or match["loser"] == team.name:
            out.append(match)
    return out
# %% markdown
#### We use the list of curated teams to figure out the actual "tier" of a team by checking how many games a team has won against tier 1/tier 2/tier 3 teams
# %% codecell
def find_tier(team,tier_weights):
    tier = 0
    data = {"tier1":{"wins":0,"losses":0},"tier2":{"wins":0,"losses":0},"tier3":{"wins":0,"losses":0}}
    for game in find_recents(team):
        if game["winner"] == team.name:
            if game["loser"] in tiers["tier1"]:
                data["tier1"]["wins"] += 1
                tier += tier_weights["tier1"]["win"]
            elif game["loser"] in tiers["tier2"]:
                data["tier2"]["wins"] += 1
                tier += tier_weights["tier2"]["win"]
            else:
                data["tier3"]["wins"] += 1
                tier += tier_weights["tier3"]["win"]
        else:
            if game["winner"] in tiers["tier1"]:
                data["tier1"]["losses"] += 1
                tier -= tier_weights["tier1"]["loss"]
            elif game["winner"] in tiers["tier2"]:
                data["tier2"]["losses"] += 1
                tier -= tier_weights["tier2"]["loss"]
            else:
                data["tier3"]["losses"] += 1
                tier -= tier_weights["tier3"]["loss"]
    return tier,data
# %% markdown
#### We then use this, and data that describes the recent form of a team, to calculate a normalized "form" value
# %% codecell
def norm_form(team,
            tier_min = 12,tier_max=40,
            sig_winstreak=5,winstreak_weight=4,last3monthsweight=1,
            tier_weights={"tier1":{"win":3,"loss":1},"tier2":{"win":2,"loss":2},"tier3":{"win":0,"loss":3}}):
    #recent form
    recent_form = (winstreak_weight*(float(team.stats["winstreak"])/sig_winstreak) + last3monthsweight * float(team.stats["win%last3months"]))/100
    relative_tier = (find_tier(team,tier_weights)[0]+tier_min)/tier_max
    normalized_form = recent_form*relative_tier
    return normalized_form
# %% markdown
#### We calculate the "on paper" win/loss probability of two teams using the hltv rating and the seed of the teams
# %% codecell
def on_paper(team1,team2,hltv_weight=0.8,seed_weight=0.2):
    total_hltv = team1.stats["hltv"] + team2.stats["hltv"]
    team1_hltv = team1.stats["hltv"]/total_hltv
    team2_hltv = team2.stats["hltv"]/total_hltv

    total_seed = team1.seed + team2.seed
    team1_seed = 1-(team1.seed/total_seed)
    team2_seed = 1-(team2.seed/total_seed)
    team1_total = (team1_seed * seed_weight + team1_hltv * hltv_weight)/(hltv_weight + seed_weight)
    team2_total = (team2_seed * seed_weight + team2_hltv * hltv_weight)/(hltv_weight + seed_weight)
    return team1_total/(team1_total + team2_total)
# %% markdown
#### Find any historical matches
# %% codecell
def get_history(team1,team2):
    wins = 0
    losses = 0
    for match in find_recents(team1):
        if match["winner"] == team1.name and match["loser"] == team2.name:
            wins += 1
        if match["loser"] == team1.name and match["winner"] == team2.name:
            losses += 1
    if (wins + losses) == 0:
        return 0.5
    else:
        return wins/(wins+losses)
# %% markdown
#### Calculate the "variability" of a team (a measure of the experience levels of the team)
# %% codecell
def variabililty(team,worldrankingmax=53,weekstop30max=211,major_effect=2,optimal_age=26):
    rank = (worldrankingmax - team.stats["worldranking"])/worldrankingmax
    weekstop30 = (team.stats["weekstop30"]+major_effect)/(weekstop30max+major_effect)
    age = 1-(abs(team.stats["averageplayerage"]-optimal_age)/optimal_age)
    return (1 - (rank*weekstop30*age))**2
# %% markdown
#### Calculate the win probability as a combination of the above
# %% codecell
def rate(team1,team2,history_weight=0.1,form_weight=3,var_weight=1,upset_weight=0.2):
    team1rate = on_paper(team1,team2)
    team2rate = 1-team1rate
    historyteam1 = get_history(team1,team2)
    historyteam2 = 1-historyteam1
    team1rate += historyteam1*history_weight
    team2rate += historyteam2*history_weight
    total = team1rate + team2rate
    team1rate /= total
    team2rate /= total
    team1form = norm_form(team1)
    team2form = norm_form(team2)
    team1rate += team1form * form_weight
    team2rate += team2form * form_weight
    total = team1rate + team2rate
    team1rate /= total
    team2rate /= total
    team1var = variabililty(team1)
    temp = team1var
    team2var = variabililty(team2)
    team1var = team1var/team2var
    team2var = team2var/temp
    total = team1var + team2var
    team1var = team1var/total
    team2var = team2var/total
    if team1rate > team2rate:
        bad_game_chance = team1var
        good_game_chance = 1-team2var
        upset_chance = bad_game_chance*good_game_chance
        team2rate += upset_chance * upset_weight
    elif team1rate < team2rate:
        bad_game_chance = team2var
        good_game_chance = 1-team1var
        upset_chance = bad_game_chance*good_game_chance
        team1rate += upset_chance * upset_weight
    total = team1rate + team2rate
    team1rate /= total
    team2rate /= total
    return team1rate,team2rate
# %% markdown
#### Function that uses the probability from the above function
# %% codecell
def simfunc(team1,team2):
    team1win,team2win = rate(team1,team2)
    bo3 = csgo_sims.isbo3(team1,team2)
    games_to_win = 1
    if bo3:
        games_to_win = 2
    team1games = 0
    team2games = 0
    team1totalrounds = 0
    team2totalrounds = 0
    while team1games != games_to_win and team2games != games_to_win:
        team1rounds = 0
        team2rounds = 0
        while team1rounds != 16 and team2rounds != 16:
            if uniform(0,1) < team1win:
                team1rounds += 1
            else:
                team2rounds += 1
        team1totalrounds += team1rounds
        team2totalrounds += team2rounds
        if team1rounds > team2rounds:
            team1games += 1
        else:
            team2games += 1
    if team1games > team2games:
        return team1,csgo_sims.GameStats(team1totalrounds-team2totalrounds,(team1games,team2games))
    else:
        return team2,csgo_sims.GameStats(team2totalrounds-team1totalrounds,(team2games,team1games))
# %% markdown
#### Run simulation
# %% codecell
results = csgo_sims.table.do_sims(simfunc,nsims=1000,file="results.txt")
