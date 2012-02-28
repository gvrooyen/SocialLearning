# Automatically rendered agent code

from moves import *
import math
import random

last_state = None
last_state_matrix = None

def move(roundsAlive, repertoire, historyRounds, historyMoves, historyActs, historyPayoffs, historyDemes, currentDeme,
         canChooseModel, canPlayRefine, multipleDemes):

    def PioneeringBi_done(entryRound):

        assert entryRound == 0
        # Exit condition 1: The agent is a pioneer, and N_rounds rounds have elapsed
        if (roundsAlive >= 15) and (historyActs[0] == -1):
            return (1,15)
        # Exit condition 2: We've tested, and the agent is not a pioneer
        elif (len(historyActs) > 0) and (historyActs[0] > -1):
            return (2,roundsAlive)
        # Otherwise, remain in the current state
        else:
            return 0

    def DiscreteDistributionH_done(entryRound):

        return False    # Terminal trait

    def StudyB_done(entryRound):

        # print entryRound, 10, historyRounds[-1]
        if len(historyRounds) == 0:
            return False
        if entryRound + 10 > historyRounds[-1]:
            # We haven't made a move yet
            return False
        else:
            return (1,entryRound + 10)

    def DiscreteDistribution_done(entryRound):

        return False    # Terminal trait

    def DiscreteDistributionB_done(entryRound):

        return False    # Terminal trait

    state_matrix = []

    state_matrix.append(('PioneeringBi', PioneeringBi_done, [1, 1]))

    state_matrix.append(('DiscreteDistributionH', DiscreteDistributionH_done, []))

    state_matrix.append(('StudyB', StudyB_done, [3]))

    state_matrix.append(('DiscreteDistribution', DiscreteDistribution_done, []))

    state_matrix.append(('DiscreteDistributionB', DiscreteDistributionB_done, []))
    
    def traverse_states(state_matrix, state_idx = 0, entry_round = 0, recursion_depth = 0):
        if recursion_depth > 128:
            raise RuntimeError("Maximum state graph recursion reached (most likely due to an infinite state graph loop")
        done = state_matrix[state_idx][1](entry_round)
        if not done:
            return state_matrix[state_idx][0]
        else:
            # Traverse the state graph further by recursion. done[0] gives the number (1,2,3...) of the currently
            # considered state's output condition. state_matrix[state_idx][2][done[0]-1] translates into the
            # corresponding output state's index in state_matrix. done[1] is the round at which that next step
            # started running.
            return traverse_states(state_matrix, state_matrix[state_idx][2][done[0]-1], done[1], recursion_depth+1)
    
    state = traverse_states(state_matrix)
    
    


    if state == 'PioneeringBi':

        if roundsAlive == 0:
            return (OBSERVE, )
        else:
            return (INNOVATE, )


    elif state == 'DiscreteDistributionH':

        interval = [0.161946949466, 0.0287143990619, 0.89873968717, 0.81975289628]

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


    elif state == 'StudyB':

        interval = [0.289685022444, 0.712402957797, 0.379019625895]

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


    elif state == 'DiscreteDistribution':

        interval = [0.30737662505, 0.428716274076, 0.482702739551, 0.556004090613]

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


    elif state == 'DiscreteDistributionB':

        interval = [0.995767058423, 0.856722286773, 0.523179710335, 0.33684520304]

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


    else:
        raise AgentError('No such state: %s' % state)

    
def observe_who(exploiterData):
        return sorted(exploiterData,key=lambda x:x[TOTAL_PAY],reverse=True)
    

