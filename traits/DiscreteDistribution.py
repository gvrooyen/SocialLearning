from solegene import *
from moves import *
import random

class DiscreteDistribution(Trait):

    @property
    def constraints(self):
        return ('terminal')

    @property
    def evolvables(self):
        return {'Pi': (float, 0., 1.),
                'Po': (float, 0., 1.),
                'Pe': (float, 0., 1.)}
    
    def __init__(self):
        self.Pi = 0.25
        self.Po = 0.25
        self.Pe = 0.25

    def done(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        return False    # Terminal trait
    
    def move(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        interval = [self.Pi, self.Pi + self.Po, self.Pi + self.Po + self.Pe]
        if not canPlayRefine:
            # Renormalise
            interval /= interval[-1]
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
