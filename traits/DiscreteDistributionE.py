from solegene import *
from moves import *
import random

class DiscreteDistributionE(Trait):

    """
    This trait is identical to the DiscreteDistribution trait. This duplicate allows a parallel version
    of the trait to evolve separately, and both versions can occur simultaneously in the state graph.

    This version of the trait gives added initial weight to REFINE.
    """

    @property
    def constraints(self):
        return ('terminal')

    @property
    def N_transitions(self):
        return 0

    @property
    def evolvables(self):
        return {'Pi': (float, 0., 1.),
                'Po': (float, 0., 1.),
                'Pe': (float, 0., 1.),
                'Pr': (float, 0., 1.)}
    
    def __init__(self):
        self.Pi = random.random()
        self.Po = random.random()
        self.Pe = random.random()
        self.Pr = 1+random.random()

    def done(self, entryRound,
             roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        return False    # Terminal trait
    
    def move(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        interval = [self.Pi, self.Po, self.Pe, self.Pr]

        for i in xrange(1,4):
            interval[i] = interval[i-1] + interval[i]

        # Normalise the intervals
        if canPlayRefine:
            interval = [x/interval[-1] for x in interval]
        else:
            interval = [x/interval[-2] for x in interval]
        
        # If the repertoire is empty, only Pi or Po should be chosen:
        if len(repertoire) == 0:
            interval = [x/interval[-3] for x in interval]

        roll = random.random()

        if roll <= interval[0]:
            return (INNOVATE, )
        elif roll <= interval[1]:
            return (OBSERVE, )
        elif roll <= interval[2]:
            return (EXPLOIT, max(repertoire, key=repertoire.get))
        elif (roll <= interval[3]) and canPlayRefine:   # Add the sanity check in case of rounding errors
            return (REFINE, max(repertoire, key=repertoire.get))
        else:
            # Catch-all for rounding errors
            return (EXPLOIT, max(repertoire, key=repertoire.get))
