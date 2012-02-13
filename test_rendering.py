import traits
import solegene
import md5
import simulate
import networkx as nwx

G = solegene.Genome()

G.traits['PioneeringBi'] = traits.PioneeringBi.PioneeringBi()
G.traits['PioneeringBi'].N_rounds = 3

G.traits['Specialisation'] = traits.Specialisation.Specialisation()
G.traits['SpecialisationB'] = traits.SpecialisationB.SpecialisationB()

G.traits['DiscreteDistribution'] = traits.DiscreteDistribution.DiscreteDistribution()
G.traits['DiscreteDistributionB'] = traits.DiscreteDistributionB.DiscreteDistributionB()
G.traits['DiscreteDistributionC'] = traits.DiscreteDistributionC.DiscreteDistributionC()
G.traits['DiscreteDistributionD'] = traits.DiscreteDistributionD.DiscreteDistributionD()
G.traits['DiscreteDistributionE'] = traits.DiscreteDistributionE.DiscreteDistributionE()
G.traits['DiscreteDistributionF'] = traits.DiscreteDistributionF.DiscreteDistributionF()
G.traits['DiscreteDistributionG'] = traits.DiscreteDistributionG.DiscreteDistributionG()
G.traits['DiscreteDistributionH'] = traits.DiscreteDistributionH.DiscreteDistributionH()

G.state = [('PioneeringBi', ['Specialisation', 'SpecialisationB']),
           ('Specialisation', ['DiscreteDistribution','DiscreteDistributionB','DiscreteDistributionC','DiscreteDistributionD']),
           ('SpecialisationB', ['DiscreteDistributionE','DiscreteDistributionF','DiscreteDistributionG','DiscreteDistributionH']),
           ('DiscreteDistribution', []),
           ('DiscreteDistributionB', []),
           ('DiscreteDistributionC', []),
           ('DiscreteDistributionD', []),
           ('DiscreteDistributionE', []),
           ('DiscreteDistributionF', []),
           ('DiscreteDistributionG', []),
           ('DiscreteDistributionH', []),
          ]

code = G.render(debug = True)
agent_hash = md5.md5(code)
agent_name = 'agent_' + agent_hash.hexdigest()
agent_path = 'agents/rendered/' + agent_name + '.py'
print("Simulating %s..." % agent_name)

f = open(agent_path, 'w')
f.write(code)
f.close()

agent = __import__('agents.rendered.'+agent_name, fromlist=['*'])
simulate.agent = agent
simulation = simulate.Simulate(N_rounds=10000)
simulation.run(N_rounds=1000)
simulation.run(N_rounds=10)

print(zip(simulation.demes[0].population[0].historyRounds, simulation.demes[0].population[0].historyStates, simulation.demes[0].population[0].historyMoves))
