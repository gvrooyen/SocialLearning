import solegene
import md5
import simulate
import pprint
import traits.Pioneering
import traits.ExploitGreedy
import traits.DiscreteDistribution
import traits.Study

def trace(code):
    agent_hash = md5.md5(code)
    agent_name = 'agent_' + agent_hash.hexdigest()
    agent_path = 'agents/rendered/agent_debug.py'
    print("Simulating %s..." % agent_name)

    f = open(agent_path, 'w')
    f.write(code)
    f.close()

    agent = __import__('agents.rendered.agent_debug', fromlist=['*'])
    simulate.agent = agent
    simulate.N_POPULATION = 100
    simulation = simulate.Simulate(N_rounds=25, P_c = 0.1, birth_control = False)
    simulation.run()

    print(pprint.pformat(zip(simulation.demes[0].population[0].historyRounds,
                             simulation.demes[0].population[0].historyStates,
                             simulation.demes[0].population[0].historyMoves,
                             simulation.demes[0].population[0].historyActs,
                             simulation.demes[0].population[0].historyPayoffs)))

pioneering = traits.Pioneering.Pioneering()
pioneering.N_rounds = 3

G = solegene.Genome()
G.state = [('Pioneering', ['ExploitGreedy']),
           ('ExploitGreedy', ['Study']),
           ('Study', ['ExploitGreedy']),
           # ('DiscreteDistribution', [])
          ]
G.traits['Pioneering'] = pioneering
G.traits['ExploitGreedy'] = traits.ExploitGreedy.ExploitGreedy()
G.traits['Study'] = traits.Study.Study()
# G.traits['DiscreteDistribution'] = traits.DiscreteDistribution.DiscreteDistribution()

G.traits['Study'].N_rounds = 2

code = G.render(debug = True)

trace(code)
