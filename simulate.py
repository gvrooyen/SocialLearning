from moves import *
import agent
import random
from scipy.stats import poisson

N_ACTS = 100
N_POPULATION = 100
N_ROUNDS = 10000
N_OBSERVE = 3
MODE_SPATIAL = False
MODE_CUMULATIVE = False

def randpayoff(distribution = 'default'):
    if (distribution == 'default'):
        return int(random.expovariate(0.1)) 
        
class NotImplementedError(Exception):
    pass

class Individual:
    def __init__(self):
        self.roundsalive = 0
        self.repertoire = {}
        self.refinements = {}
        self.historyrounds = []
        self.historymoves = []
        self.historyacts = []
        self.deme = 0
        
        # We store a set of acts that the individual hasn't learned yet. The
        # innovate() function will random select an act from this set, learn
        # its payoff, and remove the act from the set.
        self.unknown_acts = set(range(0, N_ACTS)
    
    def reproduce(self):
        """
        Returns True if this individual should reproduce, based on its
        total lifetime payoff.
        """
        raise NotImplementedError()
        
    def innovate(self,  acts):
            
        
class Deme:
    
    def __init__(self):
        self.acts = [randpayoff() for x in range(0, N_ACTS)]
        self.population = [Individual() for x in range(0,  N_POPULATION)]

    def modify_environment(self):
        for i in range(0, N_ACTS):
            if (random.random() <= self.p_c):
                self.acts[i] = randpayoff()


class Simulate:
    
    def __init__(self):
        self.mode_spatial = MODE_SPATIAL
        self.mode_cumulative = MODE_CUMULATIVE
        
        if (self.mode_spatial):
            self.N_demes = 3
        else:
            self.N_demes = 1
        
        self.demes = [Deme() for x in range(0, self.N_demes)]
        
        self.round = 0
        self.p_c = 0.001    # Probability that the basic payoff of an act will change in a single simulation round
        
    def modify_environment(self):
        for d in range(0, N_demes):
            self.demes[d].modify_environment
    
    def migrate(self):
        raise NotImplementedError()
    
    def step(self):
        self.round += 1
        
        for d in range(0,  N_demes):
            for individual in self.demes[d].population:
                individual.roundsalive += 1
                move_act = agent.xmove(individual.roundsalive, 
                                      individual.repertoire, 
                                      individual.historyrounds,
                                      individual.historymoves, 
                                      individual.historyacts
                                      )
                if (move_act[0] == OBSERVE):
                    for i in range(0, N_OBSERVE):
                        raise NotImplementedError()
                else:
                    individual.historyrounds += individual.roundsalive
                    individual.historymoves += move_act
                    
                    if (move_act[0] == INNOVATE):
                        """
                        INNOVATE selects a new act at random from those acts not currently present in
                        the individual’s repertoire and adds that act and its exact payoff to the
                        behavioural repertoire of the individual. If an individual already
                        has the 100 possible acts in its repertoire, it gains no new act from playing
                        INNOVATE. In the cumulative case, the new act is acquired with refinement level 0.
                        """
                        if (len(individual.unknown_acts) > 0):
                            act = random.sample(individual.unknown_acts, 1)[0]
                            individual.repertoire[act] = self.demes[d].acts[act]
                            if self.mode_cumulative:
                                individual.refinements[act] = 0
                            individual.unknown_acts.remove(act)
                                
                    elif (move_act[0] == EXPLOIT):
                        raise NotImplementedError()
                    elif (move_act[0] == REFINE):
                        raise NotImplementedError()
                    else:
                        raise AttributeError('Unknown action %d',  move_act[0])
                if individual.reproduce():
                    self.demes[d].population += Individual()
        
        self.modify_environment()
        
        if (self.mode_spatial):
            self.migrate()
    
    def run(self):
        for i in range(0, N_ROUNDS):
            self.step()
