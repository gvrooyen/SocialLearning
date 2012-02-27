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
        if (roundsAlive >= 13) and (historyActs[0] == -1):
            return (1,13)
        # Exit condition 2: We've tested, and the agent is not a pioneer
        elif (len(historyActs) > 0) and (historyActs[0] > -1):
            return (2,roundsAlive)
        # Otherwise, remain in the current state
        else:
            return 0

    def Study_done(entryRound):

        if len(historyRounds) == 0:
            return False
        elif entryRound + 14 > historyRounds[-1]:
            # We haven't made a move yet
            return False
        else:
            return (1,entryRound + 14)

    def ExploitGreedy_done(entryRound):

        try:
            idx_entryRound = historyRounds.index(entryRound)
        except ValueError:
            # We haven't made a move yet, give us a chance first!
            return False
        if (roundsAlive <= entryRound):
            # No move yet
            return False
        else:
            initial_payoff = historyPayoffs[idx_entryRound+1]
            result = False
            for (change_round,payoff) in zip(historyRounds[idx_entryRound+1:],historyPayoffs[idx_entryRound+1:]):
                if payoff < initial_payoff:
                    result = True
                    break
            if result == True:
                #print ("Entered at round %d, changed at round %d. Initial payoff %d, final payoff %d." 
                #    % (entryRound, change_round, initial_payoff, payoff))
                return (1, change_round)
            else:
                return False

    def ExploitGreedyB_done(entryRound):

        idx_entryRound = historyRounds.index(entryRound)
        if (roundsAlive <= entryRound):
            # Give us a chance first!
            return False
        else:
            initial_payoff = historyPayoffs[idx_entryRound+1]
            result = False
            for (change_round,payoff) in zip(historyRounds[idx_entryRound+1:],historyPayoffs[idx_entryRound+1:]):
                if payoff < initial_payoff:
                    result = True
                    break
            if result == True:
                #print ("Entered at round %d, changed at round %d. Initial payoff %d, final payoff %d." 
                #    % (entryRound, change_round, initial_payoff, payoff))
                return (1, change_round)
            else:
                return False

    def Specialisation_done(entryRound):

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

    def DiscreteDistributionB_done(entryRound):

        return False    # Terminal trait

    def DiscreteDistribution_done(entryRound):

        return False    # Terminal trait

    def DiscreteDistributionG_done(entryRound):

        return False    # Terminal trait

    def DiscreteDistributionD_done(entryRound):

        return False    # Terminal trait

    def DiscreteDistributionE_done(entryRound):

        return False    # Terminal trait

    def DiscreteDistributionF_done(entryRound):

        return False    # Terminal trait

    def DiscreteDistributionH_done(entryRound):

        return False    # Terminal trait

    state_matrix = []

    state_matrix.append(('PioneeringBi', PioneeringBi_done, [4, 2]))

    state_matrix.append(('Study', Study_done, [11]))

    state_matrix.append(('ExploitGreedy', ExploitGreedy_done, [11]))

    state_matrix.append(('ExploitGreedyB', ExploitGreedyB_done, [4]))

    state_matrix.append(('Specialisation', Specialisation_done, [2, 1, 2, 11]))

    state_matrix.append(('DiscreteDistributionB', DiscreteDistributionB_done, []))

    state_matrix.append(('DiscreteDistribution', DiscreteDistribution_done, []))

    state_matrix.append(('DiscreteDistributionG', DiscreteDistributionG_done, []))

    state_matrix.append(('DiscreteDistributionD', DiscreteDistributionD_done, []))

    state_matrix.append(('DiscreteDistributionE', DiscreteDistributionE_done, []))

    state_matrix.append(('DiscreteDistributionF', DiscreteDistributionF_done, []))

    state_matrix.append(('DiscreteDistributionH', DiscreteDistributionH_done, []))
    
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


    elif state == 'Study':

        interval = [0.586802919991, 0.450579387979, 0.448262581565]

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


    elif state == 'ExploitGreedy':

        
        # Dead simple. Exploit. The done() method will move us out of here if the payoff ever drops.

        if len(repertoire) > 0:
            return (EXPLOIT, max(repertoire, key=repertoire.get))
        else:
            return (INNOVATE,)


    elif state == 'ExploitGreedyB':

        
        # Dead simple. Exploit. The done() method will move us out of here if the payoff ever drops.

        if len(repertoire) > 0:
            return (EXPLOIT, max(repertoire, key=repertoire.get))
        else:
            return (INNOVATE,)


    elif state == 'Specialisation':

        
        # The algorithm here is identical to the one used by DiscreteDistribution

        interval = [0.560686657052, 0.713131983454, 0.382241262714, 0.560984236069]

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

        interval = [0.962978673701, 0.236894949489, 0.488008323524, 0.267267578622]

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


    elif state == 'DiscreteDistribution':

        interval = [0.292365491317, 0.339449200857, 0.131732830492, 0.376842025232]

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


    elif state == 'DiscreteDistributionG':

        interval = [0.745759680195, 0.908535217168, 0.837425652083, 0.510775971137]

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


    elif state == 'DiscreteDistributionD':

        interval = [0.437792282243, 0.635324553132, 0.942044705297, 0.66305683473]

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


    elif state == 'DiscreteDistributionE':

        interval = [0.694479182301, 0.751937866677, 0.614417769478, 1.0]

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


    elif state == 'DiscreteDistributionF':

        interval = [0.742898735461, 0.823371689314, 1.0, 0.518772438465]

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


    elif state == 'DiscreteDistributionH':

        interval = [0.467558843701, 0.296706879929, 0.992598449707, 0.999234733815]

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
        return sorted(exploiterData,key=lambda x:x[AGE],reverse=True)
    

