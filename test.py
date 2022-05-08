import csgo_sims
from random import choice,randint,uniform
csgo_sims.table.reset()
# %% codecell
hltv_only_results = csgo_sims.table.do_sims(csgo_sims.hltv_rating_only,nsims=1000)
# %% codecell
ilyas_only_results = csgo_sims.table.do_sims(csgo_sims.ilyas_rating_only,nsims=1000)
