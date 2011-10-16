from moves import *
import agent
import random
from scipy.stats import poisson

N_ACTS = 100                # Number of acts in the environment's repertoire
N_POPULATION = 100          # Population size of a single deme
N_ROUNDS = 10000            # Number of rounds in the simulation
N_OBSERVE = 3               # Number of exploiters observed at a time; range [1-10]
MODE_SPATIAL = False        # Whether demes are enabled
MODE_CUMULATIVE = False     # Whether REFINE is available
MODE_MODEL_BIAS = False     # Whether observe_who() can be specified
P_COPYFAIL = 0.1            # Chance of observation failure; range [0.0-0.5]
P_DEATH = 0.02              # Chance that an individual dies each round
P_MUTATE = 1.0/50.0         # Chance that a competitive strategy will be adopted in offspring
N_MIGRATE = 5               # Number of individuals migrating each round

def randpayoff(distribution = 'default'):
    if (distribution == 'default'):
        return int(random.expovariate(0.1)+1.0) 
        
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
        self.historyPayoffs = []
        self.historyDemes = []
        self.deme = 0
        self.lifetime_payoff = 0
        
        # We store a set of acts that the individual hasn't learned yet. The
        # innovate() function will random select an act from this set, learn
        # its payoff, and remove the act from the set.
        self.unknownActs = set(range(0, N_ACTS))
            
        
class Deme:
    
    def __init__(self):
        self.acts = [randpayoff() for x in range(0, N_ACTS)]
        self.population = [Individual() for x in range(0,  N_POPULATION)]
        self.stat_act_updates = 0

    def modify_environment(self, p_c = P_COPYFAIL):
        for i in range(0, N_ACTS):
            if (random.random() <= p_c):
                self.acts[i] = randpayoff()
                self.stat_act_updates += 1  # Keep track of act update statistics


class Simulate:
    
    def __init__(self, mode_spatial = MODE_SPATIAL, 
                       mode_cumulative = MODE_CUMULATIVE,
                       mode_model_bias = MODE_MODEL_BIAS, 
                       N_observe = N_OBSERVE, 
                       P_copyFail = P_COPYFAIL, 
                       N_rounds = N_ROUNDS, 
                       P_death = P_DEATH, 
                       N_migrate = N_MIGRATE,
                       birth_control = False):
        self.mode_spatial = mode_spatial
        self.mode_cumulative = mode_cumulative
        self.mode_model_bias = mode_model_bias
        self.N_observe = N_observe
        self.P_copyFail = P_copyFail
        self.N_rounds = N_rounds
        self.P_death = P_death
        self.N_migrate = N_migrate
        self.birth_control = birth_control  # Set to True to suppress new births in this simulation
        self.total_payoff = 0
        
        self.stat_deaths = {}
        self.stat_births = {}
        
        if (self.mode_spatial):
            self.N_demes = 3
        else:
            self.N_demes = 1
        
        self.demes = [Deme() for x in range(0, self.N_demes)]
        
        self.round = 0
        self.p_c = 0.001    # Probability that the basic payoff of an act will change in a single simulation round
        
    def modify_environment(self):
        for d in range(0, self.N_demes):
            self.demes[d].modify_environment(self.p_c)
    
    def death_birth(self):
        self.stat_deaths[self.round] = 0    # Set the death count to zero for this round
        self.stat_births[self.round] = 0    # Set the birth count to zero for this round
        
        # Firstly, we need to calculate all individuals' mean lifetime payoffs, as well as the sum of all
        # these payoffs.
        
        MLP = {}
        MLP_total = 0
        
        for d in range(0,  self.N_demes):
            MLP[d] = {}
            for individual in self.demes[d].population:
                MLP[d][individual] = 1.0*individual.lifetime_payoff/individual.roundsAlive
                MLP_total += MLP[d][individual]
        
        for d in range(0, self.N_demes):
            births = 0
            deaths = []
            for individual in self.demes[d].population:
                if (random.random() < self.P_death):
                    deaths += [individual]
                    self.stat_deaths[self.round] += 1
                elif ((not self.birth_control) and (self.total_payoff > 0) and
                      (random.random() <= (MLP[d][individual] / MLP_total) ) ):
                    births += 1
                    self.stat_births[self.round] += 1
            
            for individual in deaths:
                self.demes[d].population.remove(individual)
                    
            for i in range(0, births):
                self.demes[d].population += [Individual()]
        
                    
    
    def migrate(self):
       
        # The migrants must first be selected (N_migrate from each deme) and then be moved. If migrants are moved
        # the moment that they are selected, there is a chance that immigrants from lower demes will repatriate
        # by being reselected for migration in their new deme.
        
        migrants = {}
        
        for d in range(0, self.N_demes):
            # Randomly pick N_migrate individuals from the current deme. They will be moved to another random deme
            # in the next loop.
            migrants[d] = random.sample(self.demes[d].population, 
                                        min(self.N_migrate, len(self.demes[d].population)))
      
        for d in range(0, self.N_demes):
            
            other_demes = range(0, self.N_demes)
            other_demes.remove(d)
                        
            for migrant in migrants[d]:
                self.demes[d].population.remove(migrant)
                self.demes[random.choice(other_demes)].population += [migrant]
            
    
    def step(self,  test_commands = None):
        """
        The optional test_commands parameter (default None) is provided to allow the test suite to dictate "canned"
        commands to the population (i.e. ignoring agent.move()'s strategy. The data structure should consist of a tuple
        of commands for each deme, showing the moves for the first few members of the population for this round, e.g.:
        
            test_commands =   ( ( (INNOVATE,), (OBSERVE,), (EXPLOIT,0), (REFINE,1) ),    # first deme
                                ( (EXPLOIT,0), (EXPLOIT, 1), (OBSERVE,), (INNOVATE,) )   # second deme
                              )
        
        This forces the first four members of the first and the second deme to make the specified moves. All other
        remaining individuals in the population are forced to play INNOVATE.
        
        """
        self.round += 1
        
        for d in range(0,  self.N_demes):
            
            observers = []
            exploiters = []
            i = 0;  # Used to keep count of individuals for when using test commands
            
            for individual in self.demes[d].population:
                individual.roundsAlive += 1
                individual.historyDemes += [d]
                
                if (test_commands == None):
                
                    move_act = agent.move(individual.roundsAlive, 
                                          individual.repertoire, 
                                          individual.historyRounds,
                                          individual.historyMoves, 
                                          individual.historyActs, 
                                          individual.historyPayoffs, 
                                          individual.historyDemes, 
                                          d, 
                                          self.mode_model_bias, 
                                          self.mode_cumulative, 
                                          self.mode_spatial
                                          )
                
                else:
                    # The test suite has provided "canned" moves for us to use
                    
                    try:
                        move_act = test_commands[d][i]
                    except IndexError:
                        move_act = (INNOVATE, )
                        
                individual.historyRounds += [individual.roundsAlive]
                individual.historyMoves += [move_act[0]]

                if (move_act[0] == INNOVATE):
                    """
                    INNOVATE selects a new act at random from those acts not currently present in
                    the individual's repertoire and adds that act and its exact payoff to the
                    behavioural repertoire of the individual. If an individual already
                    has the 100 possible acts in its repertoire, it gains no new act from playing
                    INNOVATE. In the cumulative case, the new act is acquired with refinement level 0.
                    """
                    if (len(individual.unknownActs) > 0):
                        act = random.sample(individual.unknownActs, 1)[0]
                        individual.repertoire[act] = self.demes[d].acts[act]
                        individual.historyActs += [act]
                        individual.historyPayoffs += [individual.repertoire[act]]
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
                    if individual.repertoire.has_key(move_act[1]):
                        act = move_act[1]
                        payoff = self.demes[d].acts[act]
                        if individual.refinements.has_key(act):
                            payoff += individual.refinements[act]
                        individual.historyActs += [act]
                        individual.historyPayoffs += [payoff]
                        individual.lifetime_payoff += payoff
                        self.total_payoff += payoff
                        exploiters += [individual]
                    
                elif (move_act[0] == REFINE):
                    
                    act = move_act[1]
                    
                    # An individual can only exploit an act that it has already learned
                    if (not self.mode_cumulative):
                        raise ValueError("REFINE is not available in a non-cumulative simulation.")
                    elif (not individual.repertoire.has_key(act)):
                        raise KeyError("Attempt to refine an unknown act")
                    else:
                        try:
                            individual.refinements[act] += 1
                        except KeyError:
                            individual.refinements[act] = 0
                            
                        individual.historyActs += [act]
                        individual.historyPayoffs += [self.demes[d].acts[act] + individual.refinements[act]]
                        individual.refinements[act] = individual.historyPayoffs[-1]
                    
                else:
                    raise AttributeError('Unknown action %d',  move_act[0])
                    
                i += 1  # Used to keep count of individuals for when using test commands
                
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
                        observer.repertoire[act] = observer.historyPayoffs[-1]
                        
                        # We rather use a set difference to remove the observed act from the list of
                        # unknowns, in case the agent has (suboptimally) tried to observe an event
                        # that it already knew. In such a case, unknownActs.remove(act) would raise
                        # an exception (whereas a set difference is always defined).
                        
                        observer.unknownActs -= set([act])
                        
                        exploiter.timesCopied += 1
        
        self.modify_environment()
        
        self.death_birth()
        
        if (self.mode_spatial):
            self.migrate()
    
    def run(self):
        for i in range(0, self.N_rounds):
            self.step()
