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
        if (roundsAlive >= 11) and (historyActs[0] == -1):
            return (1,11)
        # Exit condition 2: We've tested, and the agent is not a pioneer
        elif (len(historyActs) > 0) and (historyActs[0] > -1):
            return (2,roundsAlive)
        # Otherwise, remain in the current state
        else:
            return 0

    def InnovationBeat_done(entryRound):

        return False    # Terminal trait

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

    def DiscreteDistributionH_done(entryRound):

        return False    # Terminal trait

    def DiscreteDistributionG_done(entryRound):

        return False    # Terminal trait

    def Study_done(entryRound):

        if len(historyRounds) == 0:
            return False
        elif entryRound + 7 > historyRounds[-1]:
            # We haven't made a move yet
            return False
        else:
            return (1,entryRound + 7)

    def DiscreteDistributionD_done(entryRound):

        return False    # Terminal trait

    def DiscreteDistributionE_done(entryRound):

        return False    # Terminal trait

    def DiscreteDistributionC_done(entryRound):

        return False    # Terminal trait

    def DiscreteDistributionB_done(entryRound):

        return False    # Terminal trait

    def DiscreteDistributionF_done(entryRound):

        return False    # Terminal trait

    state_matrix = []

    state_matrix.append(('PioneeringBi', PioneeringBi_done, [1, 2]))

    state_matrix.append(('InnovationBeat', InnovationBeat_done, []))

    state_matrix.append(('ExploitGreedy', ExploitGreedy_done, [2]))

    state_matrix.append(('DiscreteDistributionH', DiscreteDistributionH_done, []))

    state_matrix.append(('DiscreteDistributionG', DiscreteDistributionG_done, []))

    state_matrix.append(('Study', Study_done, [3]))

    state_matrix.append(('DiscreteDistributionD', DiscreteDistributionD_done, []))

    state_matrix.append(('DiscreteDistributionE', DiscreteDistributionE_done, []))

    state_matrix.append(('DiscreteDistributionC', DiscreteDistributionC_done, []))

    state_matrix.append(('DiscreteDistributionB', DiscreteDistributionB_done, []))

    state_matrix.append(('DiscreteDistributionF', DiscreteDistributionF_done, []))
    
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


    elif state == 'InnovationBeat':


    # Firstly, we need to find a sequence of N_Seq OBSERVE actions, to decide which round is most likely to be
    # a sync round. We do this in a greedy way: if we see an OBSERVE round where no models (agents playing EXPLOIT)
    # were observe, we immediately assume that is a sync round. This has the added effect that pioneers (agents starting
    # this state in the very first round of a simulation) will start syncing on the first round.

        if roundsAlive < 2:
            return (OBSERVE,)
        else:
            start_idx = 0
            streak_found = False

            while not streak_found:
                # Try to find runs of the OBSERVE action. Note that multiple OBSERVE results may occur in a single round,
                # so we'll need to collapse these later
                try:
                    first_observe_idx = historyMoves[start_idx:].index(OBSERVE) + start_idx
                except ValueError:
                    # No OBSERVE actions remain in the history, so we need to create some
                    return (OBSERVE,)

                observe_payoffs = {}

                for idx in xrange(first_observe_idx, len(historyMoves)):
                    if historyMoves[idx] == OBSERVE:
                        round = historyRounds[idx]
                        try:
                            observe_payoffs[round] += historyPayoffs[idx]
                        except KeyError:
                            observe_payoffs[round] = historyPayoffs[idx]
                        if len(observe_payoffs) > 7:
                            streak_found = True
                    else:
                        # The OBSERVE streak has ended before it was long enough; look for the next one.
                        start_idx = idx + 1
                        break
                else:
                    if not streak_found:
                        # We're midway through an OBSERVE streak; play the next round.
                        return (OBSERVE,)

            # Efficient trick to obtain both the minimum key and value in a single traversal
            import operator
            min_round, min_payoff = min(observe_payoffs.items(), key=operator.itemgetter(1))

            # The value of the minimum round allows us to determine at what offset the "innovation beat" occurs
            # relative to this individual's first round of life. We would like to later calculate
            # e.g. [2, 1, 2, 1, 2, 2, 2, 2, 2, 2][(roundsAlive - offset) % 4] to determine what move in the sequence to play
            # recall that [2, 1, 2, 1, 2, 2, 2, 2, 2, 2][0] is the INNOVATE round).
            #
            # If the min_round was found at round 13, and N_Seq == 4, offset must be 1, so that INNOVATE can
            # again be played at round 17, because (17 - 1) % 4 is zero.

            offset = (min_round) % 7

            # The next thing we should check, is whether we've made the choice to be in group A or group B
            # yet. We do this by inspecting the moves after the OBSERVE streak (until they run out). The first
            # move that unambiguously corresponds to a move in one of the sequences (taking into account the
            # round and offset) is used to pick the sequence.
            #
            # Note that it typically doesn't matter if the OBSERVE streak was a coincidence from a previous
            # state, and that the "unambiguous correspondence" is also coincidental. It will in future associate
            # this individual with this state by the same analysis. (An exception to this assumption is if
            # a previous state deliberately plays similar OBSERVE sequences, which may disturb the A/B balance).

            last_observe_round = max(observe_payoffs.keys())

            seq = None

            for round in xrange(last_observe_round+1, historyRounds[-1]):
                idx = historyRounds.index(round)
                s = (round - offset) % 7
                m = historyMoves[idx]

                # It's no use checking for unambiguous correspondence if the sequences play the same move at
                # this point
                if [2, 1, 2, 1, 2, 2, 2, 2, 2, 2][s] != [2, 0, 2, 1, 2, 2, 2, 2, 1, 2][s]:
                    if m == [2, 1, 2, 1, 2, 2, 2, 2, 2, 2][s]:
                        seq = [2, 1, 2, 1, 2, 2, 2, 2, 2, 2]
                        break
                    elif m == [2, 0, 2, 1, 2, 2, 2, 2, 1, 2][s]:
                        seq = [2, 0, 2, 1, 2, 2, 2, 2, 1, 2]
                        break
                    else:
                        # Keep on looking
                        pass

            if not seq:
                # We didn't find any evidence that we made a choice about a group to belong to yet. Pick one!
                seq = random.choice([[2, 1, 2, 1, 2, 2, 2, 2, 2, 2], [2, 0, 2, 1, 2, 2, 2, 2, 1, 2]])

            next_move = seq[(roundsAlive - offset + 1) % 7]

            if next_move == INNOVATE:
                return (INNOVATE,)
            elif next_move == OBSERVE:
                return (OBSERVE,)
            elif len(repertoire) > 0:
                if next_move == EXPLOIT:
                    return (EXPLOIT, max(repertoire, key=repertoire.get))
                elif next_move == REFINE:
                    if canPlayRefine:
                        return (REFINE, max(repertoire, key=repertoire.get))
                    else:
                        return (EXPLOIT, max(repertoire, key=repertoire.get))
            else:
                return (INNOVATE,)


    elif state == 'ExploitGreedy':

        
        # Dead simple. Exploit. The done() method will move us out of here if the payoff ever drops.

        if len(repertoire) > 0:
            return (EXPLOIT, max(repertoire, key=repertoire.get))
        else:
            return (INNOVATE,)


    elif state == 'DiscreteDistributionH':

        interval = [0.52029410079, 0.299463843843, 0.929135250957, 0.961672636325]

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

        interval = [0.524537683326, 0.926754037292, 0.944377146699, 0.635162855686]

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


    elif state == 'Study':

        interval = [0.632559185987, 0.615269743225, 0.341390826738]

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


    elif state == 'DiscreteDistributionD':

        interval = [0.577148072315, 0.327110295606, 0.711740029128, 0.227474972715]

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

        interval = [0.71406823348, 0.490746742478, 0.721661500009, 0.717850047721]

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


    elif state == 'DiscreteDistributionC':

        interval = [0.519534574449, 0.931050423353, 0.597958296249, 0.417780048922]

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

        interval = [0.986742610388, 0.425686823839, 0.578068972521, 0.696563553623]

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

        interval = [0.890748635985, 0.510506906902, 0.871648804243, 0.536450094768]

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
        return sorted(exploiterData,key=lambda x:x[N_OFFSPRING],reverse=True)
    

