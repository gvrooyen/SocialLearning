from solegene import *
from moves import *
import random

class SpecialisationB(Trait):

    """
    This is a one-move state that randomly plays a single move from the repertoire. It then has one of four output states
    based on the move played. The choice of move is played from an evolvable distribution.
    """

    @property
    def constraints(self):
        return ('terminal')

    @property
    def N_transitions(self):
        """
        Number of output transitions of a state corresponding to this trait (default 1)
        """
        return 4

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
        self.Pr = random.random()

    def done(self, entryRound,
             roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        if roundsAlive == entryRound:
            # We haven't made a move yet
            return False
        else:
            # Inspect the move, and return the corresponding exit condition. Note that moves are defined on the range [-1,2],
            # whereas valid exit conditions start numbering at 1. Therefore, add 2 to the move's enumeration to get the exit
            # condition. Also, this state always lasts just one move.
            
            # Note that we need to index historyRounds to find out at which position of the lists round number entryRound
            # occurred. Because moves like OBSERVE can occupy several list positions, entryRound cannot simply be used
            # as the list index.

            return (historyMoves[historyRounds.index(entryRound+1)]+2, entryRound+1)
    
    def move(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        
        # The algorithm here is identical to the one used by DiscreteDistribution

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
