from moves import * #bring in standard names for moves
#this means INNOVATE, OBSERVE, EXPLOIT and REFINE can be used instead of -1,0,1,2
#and that AGE, TOTAL_PAY, TIMES_COPIED and N_OFFSPRING can be used to index into exploiterData

#imports standard random number and mathematics modules; other base modules (v2.7)
# can be imported here if needed
import math

N_ACTS = 100

random = object()

def move(roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
         canChooseModel, canPlayRefine, multipleDemes):
    """
    roundsAlive, currentDeme are integers, history* are tuples of integers
    repertoire is a dictionary with keys=behavioural acts and values=payoffs
    canChooseModel, canPlayRefine, multipleDemes are boolean, indicating whether:
    observe_who will be called (i.e. model bias), REFINE is available (i.e.
    cumulative), and multiple demes (i.e. spatial) respectively.

    This function MUST return a tuple in the form (MOVE,ACT) if MOVE is EXPLOIT or
    REFINE, or (MOVE,) if MOVE is INNOVATE or OBSERVE.
    """

    return 0


def observe_who(exploiterData):
    'This function MUST return the given list of tuples, exploiterData, sorted by preference for copying.'
    'Data given for each agent are (index in this list,age,total accrued payoff,number of times copied,number of offpsring)'
    'All values except index have error applied'

    return 0
