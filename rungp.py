import solegene
reload(solegene)

G = solegene.Genome()
G.state

GP = solegene.Generation()
GP.population[77].state

GP.step()
