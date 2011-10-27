from moves import *
import agent
import sys
import copy
import random
import traceback
from scipy.stats import poisson
from math import *

N_ACTS = 100                # Number of acts in the environment's repertoire
N_POPULATION = 100          # Population size of a single deme
N_ROUNDS = 10000            # Number of rounds in the simulation
N_OBSERVE = 3               # Number of exploiters observed at a time; range [1-10]
MODE_SPATIAL = False        # Whether demes are enabled
MODE_CUMULATIVE = False     # Whether REFINE is available
MODE_MODEL_BIAS = False     # Whether observe_who() can be specified
P_C = 0.001                 # Probability that the payoff of an act will change in a given round
P_COPYFAIL = 0.1            # Chance of observation failure; range [0.0-0.5]
P_DEATH = 0.02              # Chance that an individual dies each round
P_MUTATE = 1.0/50.0         # Chance that a competitive strategy will be adopted in offspring
N_MIGRATE = 5               # Number of individuals migrating each round
R_MAX = 100                 # Maximum refinement level
MEAN_PAYOFF = 10            # Mean of the basic payoff distribution

def old_copy_error(x):
    # We make the assumption that the data point "0" can be copied (it often has to be), even though the Poisson
    # distribution is not defined for this mean. However, the distribution is defined for very small means, in which
    # it, in the limit, always returns zero.
    #
    # This is the old version of the function, which uses the SciPy implementation. This version is not thread-safe,
    # and cannot be used for repeatable runs in a multiprocessed simulation.
    try:
        return poisson.rvs(x)
    except ValueError:
        return 0

def gammaln(xx):
    """
    Returns the natural logarithm of the gamma function of the argument.
    The code used here is adapted from Numerical Recipes in C [gammln()]
    """
    
    coef = [76.18009172947146,
            -86.50532032941677,
            24.01409824083091,
            -1.231739572450155,
            0.1208650973866179e-2,
            -0.5395239384953e-5]
    y = xx
    x = xx
    tmp = x + 5.5
    tmp -= (x+0.5) * log(tmp)
    ser = 1.000000000190015
    for j in range(0,6):
        y += 1.0
        ser += coef[j]/y
    return -tmp + log(2.5066282746310005*ser/x)
    

def copy_error(xm, func_random):
    """
    Returns a sample from a Poisson distribution with a mean of xm.
    The code used here is adapted from Numerical Recipes in C [poidev()]
    """
    
    oldm = -1.0
    
    if (xm < 12.0):
        if (xm != oldm):
            oldm = xm
            g = exp(-xm)
        em = -1
        t = 1.0
        while True:
            em += 1.0
            t *= func_random()
            if (t <= g):
                break
    else:
        if (xm != oldm):
            oldm = xm
            sq = sqrt(2.0*xm)
            alxm = log(xm)
            g = xm * alxm - gammaln(xm+1.0)
        while True:
            while True:
                y = tan(pi*func_random())
                em = sq * y + xm
                if (em >= 0.0):
                    break
            em = floor(em)
            t = 0.9 * (1.0+y*y) * exp(em*alxm-gammaln(em+1.0)-g)
            if (func_random() <= t):
                break
    return em;
    
        
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
    
    def randpayoff(self, distribution = 'default'):
        if (distribution == 'default'):
            return int(self.random.expovariate(1.0/MEAN_PAYOFF)+1.0)

    def __init__(self, parent):
        # Use the same random number object as the parent to ensure repeatability
        self.random = parent.random
        
        x = self.random.expovariate(0.0001)

        self.acts = [self.randpayoff() for x in range(0, N_ACTS)]
        self.population = [Individual() for x in range(0,  N_POPULATION)]
        self.stat_act_updates = 0
        
    def modify_environment(self, P_c = P_C):
        for i in range(0, N_ACTS):
            if (self.random.random() <= P_c):
                self.acts[i] = self.randpayoff()
                self.stat_act_updates += 1  # Keep track of act update statistics


class Simulate:
    
    # TODO: Add a Random() object, so that random state isn't shared between Simulate() instances.
    #       This will make tests repeatable during multiprocessed simulation runs.
    
    def __init__(self, mode_spatial = MODE_SPATIAL, 
                       mode_cumulative = MODE_CUMULATIVE,
                       mode_model_bias = MODE_MODEL_BIAS, 
                       N_observe = N_OBSERVE, 
                       P_c = P_C,
                       P_copyFail = P_COPYFAIL, 
                       N_rounds = N_ROUNDS, 
                       P_death = P_DEATH, 
                       N_migrate = N_MIGRATE,
                       r_max = R_MAX,
                       birth_control = False,
                       seed = None):
        self.mode_spatial = mode_spatial
        self.mode_cumulative = mode_cumulative
        self.mode_model_bias = mode_model_bias
        self.N_observe = N_observe
        self.P_c = P_c
        self.P_copyFail = P_copyFail
        self.N_rounds = N_rounds
        self.P_death = P_death
        self.N_migrate = N_migrate
        self.birth_control = birth_control  # Set to True to suppress new births in this simulation
        self.total_payoff = 0
        self.r_max = r_max
        
        self.random = random.Random(seed)
        
        self.stat_deaths = {}
        self.stat_births = {}
        self.stat_population = {}
        self.stat_total_OBSERVEs = 0
        self.stat_failed_copies = 0
        
        self.exception = None
        
        if (self.mode_spatial):
            self.N_demes = 3
        else:
            self.N_demes = 1
        
        self.demes = [Deme(self) for x in range(0, self.N_demes)]
        
        self.round = 0
        
    def modify_environment(self):
        for d in range(0, self.N_demes):
            self.demes[d].modify_environment(self.P_c)
    
    def payoff_increment(self, r):
        """
        Calculate the increment in payoff due to the refinement r of an act
        """
        P_max = MEAN_PAYOFF * 50
        
        i = 0
        for j in range(1, r+1):
            i += 0.95 ** (r-j)
        
        i *= 0.05*P_max/(1.0 - (0.95 ** self.r_max))
        
        return int(round(i))
    
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
                if (self.random.random() < self.P_death):
                    deaths += [individual]
                    self.stat_deaths[self.round] += 1
                elif ((not self.birth_control) and (MLP_total > 0) and
                      (self.random.random() <= (MLP[d][individual] / MLP_total) ) ):
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
            migrants[d] = self.random.sample(self.demes[d].population, 
                                        min(self.N_migrate, len(self.demes[d].population)))
      
        for d in range(0, self.N_demes):
            
            other_demes = range(0, self.N_demes)
            other_demes.remove(d)
                        
            for migrant in migrants[d]:
                self.demes[d].population.remove(migrant)
                self.demes[self.random.choice(other_demes)].population += [migrant]
            
    
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
        
        self.stat_population[self.round] = sum([len(d.population) for d in self.demes])
        
        # # Uncomment To test fitness.py's error handling and logging
        # if (self.random.random() < 0.0001):
        #    raise ValueError("This is a random error!")
        
        for d in range(0,  self.N_demes):
            
            observers = []
            exploiters = []
            i = 0;  # Used to keep count of individuals for when using test commands
            
            for individual in self.demes[d].population:
                individual.roundsAlive += 1
                
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
                                        
                if (move_act[0] == INNOVATE):
                    """
                    INNOVATE selects a new act at random from those acts not currently present in
                    the individual's repertoire and adds that act and its exact payoff to the
                    behavioural repertoire of the individual. If an individual already
                    has the 100 possible acts in its repertoire, it gains no new act from playing
                    INNOVATE. In the cumulative case, the new act is acquired with refinement level 0.
                    """
                    
                    individual.historyRounds += [individual.roundsAlive]
                    individual.historyMoves += [INNOVATE]                                        
                    individual.historyDemes += [d]
                    
                    if (len(individual.unknownActs) > 0):
                        act = self.random.sample(individual.unknownActs, 1)[0]
                        individual.repertoire[act] = self.demes[d].acts[act]
                        individual.historyActs += [act]
                        individual.historyPayoffs += [individual.repertoire[act]]
                        if self.mode_cumulative:
                            individual.refinements[act] = 0
                        individual.unknownActs.remove(act)
                    else:
                        # There's nothing left to learn -- return -1
                        individual.historyActs += [-1]
                        individual.historyPayoffs += [-1]
                        
                        
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
                            payoff += self.payoff_increment(individual.refinements[act])
                        individual.historyRounds += [individual.roundsAlive]
                        individual.historyMoves += [EXPLOIT]                    
                        individual.historyActs += [act]
                        individual.historyPayoffs += [payoff]
                        individual.historyDemes += [d]
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
                        if individual.refinements[act] <= R_MAX:
                            individual.refinements[act] += 1
                        
                        # TODO: There's some repetition in history tracking -- refactor into Individual.recordHistory()
                        individual.historyRounds += [individual.roundsAlive]
                        individual.historyMoves += [REFINE]
                        individual.historyActs += [act]
                        individual.historyPayoffs += [self.demes[d].acts[act] 
                                                      + self.payoff_increment(individual.refinements[act])]
                        individual.historyDemes += [d]
                    
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
                                       copy_error(exploiter.roundsAlive, self.random.random),
                                       copy_error(sum(exploiter.historyPayoffs), self.random.random),
                                       copy_error(exploiter.timesCopied, self.random.random), 
                                       copy_error(exploiter.N_offspring, self.random.random)
                                     )]
                    i += 1
            
            # Next, resolve all observations in this deme
            for observer in observers:
                
                # FIXME: The individual's history should always contain exactly N_observe entries!
                #        If fewer than N_observe models were available, '-1' should be returned.
                
                N_succeeded = 0
                
                if self.mode_model_bias:
                    # Ask the individual whom he wants to observe
                    preferred_teachers = agent.observe_who(exploiterData)
                    exploiter_sample = [exploiters[preferred_teachers[i][0]]
                                        for i in range(0, min(self.N_observe, len(preferred_teachers)))]
                else:
                    # Default behaviour: pick N_OBSERVE exploiters at random (if there are that many)
                    exploiter_sample = self.random.sample(exploiters, min(self.N_observe, len(exploiters)))
                for exploiter in exploiter_sample:
                    # There is a random chance that we simply fail to learn by observing
                    self.stat_total_OBSERVEs += 1
                    if (self.random.random() > self.P_copyFail):
                        # Pick out the exploiter's last act and associated payoff
                        act = exploiter.historyActs[-1]
                        payoff = exploiter.historyPayoffs[-1]
                        N_succeeded += 1
                        if self.mode_cumulative and (exploiter.refinements.has_key(act)):
                            refinement = exploiter.refinements[act]
                            observer.refinements[act] = refinement
                        else:
                            refinement = 0
                            
                        # The exact payoff isn't learned; rather, a sample from a poisson distribution
                        
                        observer.historyRounds += [observer.roundsAlive]
                        observer.historyMoves += [OBSERVE]
                        observer.historyActs += [act]
                        observer.historyPayoffs += [copy_error(payoff + self.payoff_increment(refinement), 
                                                               self.random.random)]
                        observer.historyDemes += [d]
                        observer.repertoire[act] = observer.historyPayoffs[-1]
                        
                        # We rather use a set difference to remove the observed act from the list of
                        # unknowns, in case the agent has (suboptimally) tried to observe an event
                        # that it already knew. In such a case, unknownActs.remove(act) would raise
                        # an exception (whereas a set difference is always defined).
                        
                        observer.unknownActs -= set([act])
                        
                        exploiter.timesCopied += 1
                    else:
                        # Copy failed; keep track of the stats
                        self.stat_failed_copies += 1
                        
                for i in range(0, self.N_observe - N_succeeded):
                        observer.historyRounds += [observer.roundsAlive]
                        observer.historyMoves += [OBSERVE]
                        observer.historyActs += [-1]
                        observer.historyPayoffs += [-1]
                        observer.historyDemes += [d]
                    
        
        self.modify_environment()
        
        self.death_birth()
        
        if (self.mode_spatial):
            self.migrate()
    
    def run(self, silent_fail = False):
        try:
            for i in range(0, self.N_rounds):
                self.step()
        except:
            # To make run() multiprocessing-safe, it should raise no exceptions, but rather fail silently,
            # and just leave the exception information inside the object itself. To make this possible, any exception is
            # caught here, but only re-raised if we're not in "silent_fail" (multiprocessor-safe) mode.
            self.exception = traceback.format_exc()
            if not silent_fail:
                raise
