import csgo_sims
import pandas as pd
import datetime

team_stats = csgo_sims.TeamData("data/team_stats.csv")
matches = csgo_sims.Matches("data/matches.csv",types={"winner":str,"loser":str,"winnerscore":int,"loserscore":int,"date":"date","bo3":bool})
team_stats.get_elo(matches,"winner","loser","winnerscore","loserscore")

seeds = csgo_sims.SeedData("data/team_seeds.csv")
table = csgo_sims.Table(team_stats,seeds)
