from moves import *
import agent
import random
from scipy.stats import poisson

N_ACTS = 100                # Immutable
N_POPULATION = 100          # Immutable
N_ROUNDS = 10000            # Immutable
N_OBSERVE = 3               # Number of exploiters observed at a time; range [1-10]
MODE_SPATIAL = False        # Whether demes are enabled
MODE_CUMULATIVE = False     # Whether REFINE is available 
P_COPYFAIL = 0.1            # Chance of observation failure; range [0.0-0.5]

def randpayoff(distribution = 'default'):
    if (distribution == 'default'):
        return int(random.expovariate(0.1)) 
        
class NotImplementedError(Exception):
    pass

class Individual:
    def __init__(self):
        self.roundsAlive = 0
        self.timesCopied = 0
        self.N_offspring = 0
        self.repertoire = {}
        self.refinements = {}
        self.historyRounds = []
        self.historyMoves = []
        self.historyActs = []
        self.deme = 0
        
        # We store a set of acts that the individual hasn't learned yet. The
        # innovate() function will random select an act from this set, learn
        # its payoff, and remove the act from the set.
        self.unknownActs = set(range(0, N_ACTS))
    
    def reproduce(self):
        """
        Returns True if this individual should reproduce, based on its
        total lifetime payoff.
        """
        raise NotImplementedError()
        
        
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
        self.N_observe = N_OBSERVE
        self.P_copyFail = P_COPYFAIL
        
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
            
            observers = []
            exploiters = []
            
            for individual in self.demes[d].population:
                individual.roundsAlive += 1
                move_act = agent.move(individual.roundsAlive, 
                                      individual.repertoire, 
                                      individual.historyRounds,
                                      individual.historyMoves, 
                                      individual.historyActs
                                      )
                individual.historyRounds += [individual.roundsAlive]
                individual.historyMoves += move_act[0]

                if (move_act[0] == INNOVATE):
                    """
                    INNOVATE selects a new act at random from those acts not currently present in
                    the individual’s repertoire and adds that act and its exact payoff to the
                    behavioural repertoire of the individual. If an individual already
                    has the 100 possible acts in its repertoire, it gains no new act from playing
                    INNOVATE. In the cumulative case, the new act is acquired with refinement level 0.
                    """
                    if (len(individual.unknownActs) > 0):
                        act = random.sample(individual.unknownActs, 1)[0]
                        individual.repertoire[act] = self.demes[d].acts[act]
                        if self.mode_cumulative:
                            individual.refinements[act] = 0
                        individual.unknownActs.remove(act)
                        
                elif (move_act[0] == OBSERVE):
                    # We can't immediately resolve OBSERVE, because we first need to run through
                    # all individuals' moves to see who's EXPLOITing. To this end, we'll build
                    # up a list of the respective individuals OBSERVing and EXPLOITing this round,
                    # and resolve the moves later.
                    
                    observers += [individual]
                            
                elif (move_act[0] == EXPLOIT):
                    
                    # An individual can only exploit an act that it has already learned
                    if (individual.repertoire.has_key(move_act[1])):
                        act = move_act[1]
                        payoff = self.demes[d].acts[act]
                        if individual.refinements.has_key(act):
                            payoff += individual.refinements[act]
                        individual.historyActs += [act]
                        individual.historypayoffs += [payoff]
                        exploiters += [individual]
                    
                elif (move_act[0] == REFINE):
                    raise NotImplementedError()
                else:
                    raise AttributeError('Unknown action %d',  move_act[0])
                if individual.reproduce():
                    self.demes[d].population += Individual()
                
            # If we're playing in the model-bias mode, we need to build up a list of all individuals playing EXPLOIT
            # this round.    
            if self.mode_model_bias:
                exploiterData = []
                i = 0
                for exploiter in exploiters:
                    exploiterData += [(i, 
                                       poisson.rvs(exploiter.roundsAlive),
                                       poisson.rvs(sum(exploiter.historyPayoffs)),
                                       poisson.rvs(exploiter.timesCopied), 
                                       poisson.rvs(exploiter.N_offspring)
                                     )]
                    i += 1
            
            # Next, resolve all observations in this deme
            for observer in observers:
                if self.mode_model_bias:
                    # Ask the individual whom he wants to observe
                    preferred_teachers = agent.observe_who(exploiterData)
                    exploiter_sample = preferred_teachers[0:min(self.N_observe, len(preferred_teachers))]
                else:
                    # Default behaviour: pick N_OBSERVE exploiters at random (if there are that many)
                    exploiter_sample = random.sample(exploiters, min(self.N_observe, len(exploiters)))
                for exploiter in exploiter_sample:
                    # There is a random chance that we simply fail to learn by observing
                    if (random.random() > self.P_copyFail):
                        # Pick out the exploiter's last act and associated payoff
                        act = exploiter.historyActs[-1]
                        payoff = exploiter.historyPayoffs[-1]
                        if self.mode_cumulative and (exploiter.refinements.has_key(act)):
                            refinement = exploiter.refinements[act]
                            observer.refinements[act] = refinement
                        else:
                            refinement = 0
                            
                        # The exact payoff isn't learned; rather, a sample from a poisson distribution
                        observer.historyActs += [act]
                        observer.historyPayoffs += [poisson.rvs(payoff + refinement)]
                        observer.unknownActs.remove(act)
                        exploiter.timesCopied += 1
        
        self.modify_environment()
        
        if (self.mode_spatial):
            self.migrate()
    
    def run(self):
        for i in range(0, N_ROUNDS):
            self.step()
