from solegene import *
from moves import *
import random

class StudyB(Trait):

    """
    Randomly play acceptable moves, over a discrete distribution of which the weights can evolve.
    """

    @property
    def constraints(self):
        return ()

    @property
    def N_transitions(self):
        return 1

    @property
    def evolvables(self):
        return {'Pi': (float, 0., 1.),
                'Po': (float, 0., 1.),
                'Pr': (float, 0., 1.),
                'N_rounds': (int, 0, 20)}
    
    def __init__(self):
        self.Pi = random.random()
        self.Po = random.random()
        self.Pr = random.random()
        self.N_rounds = random.randint(1,20)

    def done(self, entryRound,
             roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        # print entryRound, self.N_rounds, historyRounds[-1]
        if entryRound + self.N_rounds > historyRounds[-1]:
            # We haven't made a move yet
            return False
        else:
            return (1,entryRound + self.N_rounds)
    
    def move(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        interval = [self.Pi, self.Po, self.Pr]

        for i in xrange(1,3):
            interval[i] = interval[i-1] + interval[i]

        # Normalise the intervals
        if canPlayRefine:
            interval = [x/interval[-1] for x in interval]
        else:
            interval = [x/interval[-2] for x in interval]
        
        # If the repertoire is empty, only Pi or Po should be chosen:
        if len(repertoire) == 0:
            interval = [x/interval[-2] for x in interval]

        roll = random.random()

        if roll <= interval[0]:
            return (INNOVATE, )
        elif roll <= interval[1]:
            return (OBSERVE, )
        elif (roll <= interval[2]) and canPlayRefine:   # Add the sanity check in case of rounding errors
            return (REFINE, max(repertoire, key=repertoire.get))
        else:
            # Catch-all for rounding errors
            return (INNOVATE,)
