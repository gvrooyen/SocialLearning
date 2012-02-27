from solegene import *
from moves import *
import random

class Reference(Trait):

    """
    Trait based on the reference implementation. EXPLOIT, unless the last payoff drops below a percentage
    of the mean. Then, OBSERVE again.
    """

    @property
    def constraints(self):
        return ('terminal')

    @property
    def N_transitions(self):
        return 0

    @property
    def evolvables(self):
        return {'Pr': (float, 0., 1.),
                'N_innovate': (int, 1, 10),
                'threshold': (float, 0., 1.)
                }
    
    def __init__(self):
        self.Pr = random.random()
        self.N_innovate = random.randint(0,10)
        self.threshold = random.random()

    def done(self, entryRound,
             roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):
        return False    # Terminal trait
    
    def move(self, roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
             canChooseModel, canPlayRefine, multipleDemes):

        if (roundsAlive > self.N_innovate) and (historyMoves.count(EXPLOIT) > 0):     # If this isn't my first or second roundsAlive
        
            # Calculate mean payoff from playing EXPLOIT
            myMeanPayoff = (sum([p for i, p in enumerate(historyPayoffs) if historyMoves[i] == EXPLOIT]) / 
                                float(historyMoves.count(EXPLOIT)) )
            
            # Get last payoff from EXPLOIT
            lastPayoff = historyPayoffs[len(historyMoves)-1-historyMoves[::-1].index(EXPLOIT)]
            
            lastMove = historyMoves[-1]
            
            if (lastMove == OBSERVE) or (lastPayoff >= self.threshold*myMeanPayoff):
                if (random.random() < self.Pr) and canPlayRefine:
                    # If allowed, REFINE best known act 1/20 of the time
                    return (REFINE, max(repertoire, key=repertoire.get))
                else:
                    # otherwise EXPLOIT best known act
                    return (EXPLOIT, max(repertoire, key=repertoire.get))
            else:
                # Payoffs have dropped, so OBSERVE
                return (OBSERVE, )
        elif (roundsAlive > self.N_innovate):
            return (EXPLOIT, max(repertoire, key=repertoire.get))
        else:
            # This must be the first round
            return (INNOVATE, )
            


