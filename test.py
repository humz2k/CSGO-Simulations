import csgo_sims
from random import choice,randint,uniform

csgo_sims.table.reset()

print(csgo_sims.teams["Liquid"].stats["elo"])
print(csgo_sims.teams["Astralis"].stats["elo"])

csgo_sims.elohead2head(csgo_sims.teams["Liquid"],csgo_sims.teams["Astralis"])

#hltv_only_results = csgo_sims.table.do_sims(csgo_sims.hltv_rating_only,nsims=100)
