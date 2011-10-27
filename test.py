import simulate
import agent
from moves import *
import unittest
import random
import cPickle as pickle
from math import *
import scipy.special

quickTest = False   # Used to skip unit tests that are known to be stable

TOLERANCE = 0.08    # Precision required for testing whether statistical parameters were satisfied

global stats

def troubleshoot(simulation):
    """
    Troubleshoot a simulation by dumping it to a pickle file.
    
    This function can be used for ad-hoc troubleshooting of simulations where unit tests fail.
    """
    
    f = open('log/troubleshoot.sim', 'w')
    pickle.dump(simulation, f)
    f.close()
    

@unittest.skipIf(quickTest, "in quickTest mode")
class TestStats(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def test_gammaln(self):
        y = [x*pi for x in range(1, 20)]
        
        custom_v = [simulate.gammaln(z) for z in y]
        scipy_v = [scipy.special.gammaln(z) for z in y]
        
        diff_v = [abs(custom_v[i] - scipy_v[i]) for i in range(0, len(y))]
        
        self.assertLess(max(diff_v), 1e-10)
    
    def test_copy_error(self):
        
        custom_y = simulate.copy_error(0, random.random)
        scipy_y = simulate.scipy_copy_error(0)
        
        self.assertEqual(custom_y, 0)
        self.assertEqual(scipy_y, 0)
        
        custom_y = [simulate.copy_error(5.0, random.random) for x in xrange(0, 1000000)]
        scipy_y = [simulate.scipy_copy_error(5.0) for x in xrange(0, 1000000)]
        
        custom_hist = scipy.histogram(custom_y, range=(0.5, 10.5))
        scipy_hist = scipy.histogram(scipy_y, range=(0.5, 10.5))
        
        for bin in range(0, 10):
            self.assertLess(abs(1.0 - 1.0*custom_hist[0][bin]/scipy_hist[0][bin]), 0.05)

        custom_y = [simulate.copy_error(50.0, random.random) for x in xrange(0, 1000000)]
        scipy_y = [simulate.scipy_copy_error(50.0) for x in xrange(0, 1000000)]
        
        custom_hist = scipy.histogram(custom_y, range=(30, 70))
        scipy_hist = scipy.histogram(scipy_y, range=(30, 70))
        
        for bin in range(0, 10):
            self.assertLess(abs(1.0 - 1.0*custom_hist[0][bin]/scipy_hist[0][bin]), 0.05)


@unittest.skipIf(quickTest, "in quickTest mode")
class TestMovesBasic(unittest.TestCase):
    
    def setUp(self):
        # Create a new basic simulation with parameters:
        #   mode_spatial = False
        #   mode_cumulative = False
        #   N_observe = 1
        #   P_copyFail = 0.0
        #   N_rounds = 100
        # The single deme will contain random payoffs for acts. Only a small number of rounds (100) are
        # simulated, just to test that multiround simulations run correctly.
        
        self.simulation = simulate.Simulate(N_rounds = 100, P_death = -1.0,  birth_control = True,
                                            P_copyFail = 0.0, N_observe = 1)
    
    def test_Setup(self):
        self.assertEqual(len(self.simulation.demes), 1)
        self.assertEqual(len(self.simulation.demes[0].population), 100)
        self.assertEqual(len(self.simulation.demes[0].acts), 100)
    
    def test_INNOVATE(self):
        individual = self.simulation.demes[0].population[0]

        commands = ( ( (INNOVATE, ),  ),  )
        self.simulation.step(commands)        
        
        self.assertEqual(len(individual.repertoire), 1)
        self.assertEqual(len(individual.historyActs), 1)
        self.assertEqual(len(individual.historyPayoffs), 1)
        
        self.assertListEqual(individual.historyMoves, [INNOVATE])
        self.assertListEqual(individual.historyDemes, [0])
        self.assertListEqual(individual.historyRounds, [1])
        
        learned_act = individual.historyActs[0]
        learned_payoff = individual.historyPayoffs[0]
        
        self.assertEqual(individual.repertoire[learned_act], learned_payoff)
        
    def test_INNOVATE_beyond_capacity(self):
        # Verify that, after an individual has learned 100 acts, the next act and
        # payoff returned is -1
        
        individual = self.simulation.demes[0].population[0]
        commands = ( ( (INNOVATE, ),  ),  )

        for i in range(0,100):
            self.simulation.step(commands)
            self.assertNotEqual(individual.historyActs[-1], -1)
            self.assertNotEqual(individual.historyPayoffs[-1], -1)
        
        # Eat that one bite too much
        self.simulation.step(commands)
        
        self.assertEqual(len(individual.historyActs), 101)
        self.assertEqual(len(individual.historyMoves), 101)
        self.assertEqual(len(individual.historyPayoffs), 101)
        self.assertEqual(len(individual.historyDemes), 101)
        self.assertEqual(individual.historyActs[-1], -1)
        self.assertEqual(individual.historyPayoffs[-1], -1)
        
        
    def test_EXPLOIT(self):
        individual = self.simulation.demes[0].population[0]

        commands = ( ( (INNOVATE, ),  ),  )
        self.simulation.step(commands)
        
        learned_act = individual.historyActs[0]
        
        commands = ( ( (EXPLOIT, learned_act),  ),  )
        self.simulation.step(commands)
        
        self.assertEqual(len(individual.repertoire), 1)
        self.assertEqual(len(individual.historyActs), 2)
        self.assertEqual(len(individual.historyPayoffs), 2)
        
        self.assertListEqual(individual.historyMoves, [INNOVATE, EXPLOIT])
        self.assertListEqual(individual.historyDemes, [0, 0])
        self.assertListEqual(individual.historyRounds, [1, 2])
        
        exploited_payoff = individual.historyPayoffs[1]
        self.assertEqual(individual.repertoire[learned_act], exploited_payoff)
    
        
    def test_OBSERVE(self):
        teacher = self.simulation.demes[0].population[0]
        learner = self.simulation.demes[0].population[1]

        commands = ( ( (INNOVATE, ), (INNOVATE, ) ),  )
        self.simulation.step(commands)
        
        teacher_act = teacher.historyActs[0]
        
        commands = ( ( (EXPLOIT, teacher_act), (OBSERVE, ) ),  )
        self.simulation.step(commands)

        self.assertEqual(len(teacher.repertoire), 1)
        self.assertLessEqual(len(learner.repertoire), 2)
        self.assertEqual(len(teacher.historyActs), 2)
        self.assertEqual(len(learner.historyActs), 2)
        self.assertEqual(len(teacher.historyPayoffs), 2)        
        self.assertEqual(len(learner.historyPayoffs), 2)
        
        self.assertListEqual(teacher.historyMoves, [INNOVATE, EXPLOIT])
        self.assertListEqual(learner.historyMoves, [INNOVATE, OBSERVE])
        self.assertListEqual(teacher.historyDemes, [0, 0])
        self.assertListEqual(learner.historyDemes, [0, 0])
        self.assertListEqual(teacher.historyRounds, [1, 2])
        self.assertListEqual(learner.historyRounds, [1, 2])
        
        self.assertEqual(learner.historyActs[1], teacher_act)
        self.assertTrue(learner.repertoire.has_key(teacher_act))
        
        
    def test_OBSERVE_N(self):
        self.simulation.N_observe = 3
        
        teachers = self.simulation.demes[0].population[0:3]
        learner = self.simulation.demes[0].population[3]

        commands = ( ( ( (INNOVATE, ), ) * 4 ),  )
        self.simulation.step(commands)
        
        teacher_acts = [t.historyActs[0] for t in teachers]
        
        commands = ( ( (EXPLOIT, teacher_acts[0]), 
                       (EXPLOIT, teacher_acts[1]), 
                       (EXPLOIT, teacher_acts[2]), 
                       (OBSERVE, )
                   ),)
        self.simulation.step(commands)
        
        # FIXME: Assertions are likely to fail if the individuals happen to discover the same act in the first round.
        
        for teacher in teachers:
            self.assertEqual(len(teacher.historyActs), 2)
            self.assertEqual(len(teacher.historyPayoffs), 2)        
            self.assertListEqual(teacher.historyMoves, [INNOVATE, EXPLOIT])
            self.assertListEqual(teacher.historyDemes, [0, 0])
            self.assertListEqual(teacher.historyRounds, [1, 2])

        self.assertEqual(len(learner.historyActs), 4)
        self.assertEqual(len(learner.historyPayoffs), 4)
        
        self.assertListEqual(learner.historyMoves, [INNOVATE] + [OBSERVE]*3)
        self.assertListEqual(learner.historyDemes, [0]*4)
        self.assertListEqual(learner.historyRounds, [1, 2, 2, 2])
        
        self.assertSetEqual(set(learner.historyActs[1:4]), set(teacher_acts))

        for teacher_act in teacher_acts:
            self.assertTrue(learner.repertoire.has_key(teacher_act))
        
    def test_OBSERVE_N_undersupply(self):        
        self.simulation.N_observe = 3
        
        teacher = self.simulation.demes[0].population[0]
        learner = self.simulation.demes[0].population[1]

        commands = ( ( (INNOVATE, ), (INNOVATE, ) ),  )
        self.simulation.step(commands)
        
        teacher_act = teacher.historyActs[0]
        teacher_payoff = teacher.historyPayoffs[0]
        learner_act = learner.historyActs[0]
        learner_payoff = learner.historyPayoffs[0]
        
        commands = ( ( (EXPLOIT, teacher_act), (OBSERVE, ) ),  )
        self.simulation.step(commands)

        self.assertEqual(len(teacher.repertoire), 1)
        self.assertLessEqual(len(learner.repertoire), 2)
        self.assertEqual(len(teacher.historyActs), 2)
        self.assertListEqual(learner.historyActs, [learner_act, teacher_act, -1, -1])
        self.assertEqual(len(teacher.historyPayoffs), 2)        
        self.assertListEqual(learner.historyPayoffs[2:4], [-1, -1])
        
        self.assertListEqual(teacher.historyMoves, [INNOVATE, EXPLOIT])
        self.assertListEqual(learner.historyMoves, [INNOVATE, OBSERVE, OBSERVE, OBSERVE])
        self.assertListEqual(teacher.historyDemes, [0, 0])
        self.assertListEqual(learner.historyDemes, [0, 0, 0, 0])
        self.assertListEqual(teacher.historyRounds, [1, 2])
        self.assertListEqual(learner.historyRounds, [1, 2, 2, 2])
        
    
    def test_REFINE_error(self):
        commands = ( ( (REFINE, 0),  ),  )
        
        with self.assertRaises(ValueError):
            self.simulation.step(commands)
            
            
    def test_UNKNOWN_error(self):
        commands = ( ( (999,999), ), )
        
        with self.assertRaises(AttributeError):
            self.simulation.step(commands)


    def test_REFINE_increment(self):
        """
        Verify that the function that returns payoff increments for a given level of refinement, corresponds to the
        first few hand-calculated values.
        """
        
        simulate.MEAN_PAYOFF = 10
        simulate.R_MAX = 100
        
        I = [self.simulation.payoff_increment(i) for i in range(0, 5)]
        
        self.assertListEqual(I, [0, 25, 49, 72, 93])
        
        
@unittest.skipIf(quickTest, "in quickTest mode")
class TestRunBasic(unittest.TestCase):
    
    def setUp(self):
        # Create a new basic simulation with default parameters:
        #   mode_spatial = False
        #   mode_cumulative = False
        #   N_observe = 3
        #   P_copyFail = 0.1
        #   N_rounds = 100000
        # The single deme will contain random payoffs for acts. 
        
        self.simulation = simulate.Simulate(N_rounds = 10000)
        
    def test_RunBasic(self):
        self.simulation.run()
        
        P_c_accuracy = (1.0 * self.simulation.demes[0].stat_act_updates / self.simulation.N_rounds
                        / simulate.N_ACTS / self.simulation.P_c)
        
        self.assertLess(abs(P_c_accuracy - 1.0), TOLERANCE, 
                        "P_c not simulated to within the required tolerance (%.4f)" % P_c_accuracy)
        
        P_copyFail_accuracy = (1.0 * self.simulation.stat_failed_copies / self.simulation.stat_total_OBSERVEs /
                               self.simulation.P_copyFail)
        
        self.assertLess(abs(P_copyFail_accuracy - 1.0), TOLERANCE, 
                        "P_copyFail not simulated to within the required tolerance")
        
        P_death_accuracy = (1.0 * sum(self.simulation.stat_deaths.values()) 
                               / sum(self.simulation.stat_population.values()) /
                               self.simulation.P_death)
        
        self.assertLess(abs(P_death_accuracy - 1.0), TOLERANCE, 
                               "P_death not simulated to within the required tolerance")


        # TODO: Refactor so that stat gathering and reporting can be done in one place, without duplicating the logic
        #       for each full-run test (D.R.Y.)
            
        stats['RunBasic'] = {}
        stats['RunBasic']['act_updates'] = self.simulation.demes[0].stat_act_updates
        stats['RunBasic']['N_rounds'] = self.simulation.N_rounds
        stats['RunBasic']['P_c'] = self.simulation.P_c
        stats['RunBasic']['births'] = sum(self.simulation.stat_births.values())
        stats['RunBasic']['deaths'] = sum(self.simulation.stat_deaths.values())
        stats['RunBasic']['P_death'] = self.simulation.P_death
        stats['RunBasic']['cumulative_population']  = sum(self.simulation.stat_population.values())
        stats['RunBasic']['final_population'] = len(self.simulation.demes[0].population)
        stats['RunBasic']['total_payoff'] = self.simulation.total_payoff
        stats['RunBasic']['total_OBSERVEs'] = self.simulation.stat_total_OBSERVEs
        stats['RunBasic']['failed_copies'] = self.simulation.stat_failed_copies
        stats['RunBasic']['P_copyFail'] = self.simulation.P_copyFail
        
        # Pickle the simulation object to file, for later analysis and graphing
        f = open('log/test_RunBasic.sim', 'w')
        pickle.dump(self.simulation, f)
        f.close()
    
    @staticmethod
    def printReport():
        
        if (not stats.has_key('RunBasic')):
            return
            
        print('--------------------')
        print("RunBasic - act updates: %d/%d (%.4f) for P_c=%.4f" 
              % (stats['RunBasic']['act_updates'], stats['RunBasic']['N_rounds'] * simulate.N_ACTS, 
                 1.0 * stats['RunBasic']['act_updates'] / stats['RunBasic']['N_rounds']
                 / simulate.N_ACTS, 
                 stats['RunBasic']['P_c']))
    
        print("RunBasic - failed copies: %d/%d (%.4f) for P_copyFail=%.4f" 
              % (stats['RunBasic']['failed_copies'], stats['RunBasic']['total_OBSERVEs'], 
                 1.0 * stats['RunBasic']['failed_copies'] / stats['RunBasic']['total_OBSERVEs'], 
                 stats['RunBasic']['P_copyFail']))

        print("RunBasic - deaths: %d/%d (%.4f) for P_death=%.4f" 
              % (stats['RunBasic']['deaths'], stats['RunBasic']['cumulative_population'], 
                 1.0 * stats['RunBasic']['deaths'] / stats['RunBasic']['cumulative_population'], 
                 stats['RunBasic']['P_death']))
    
        print("RunBasic - births: %d/%d (%.4f)" 
              % (stats['RunBasic']['births'], stats['RunBasic']['cumulative_population'], 
                 1.0 * stats['RunBasic']['births'] / stats['RunBasic']['cumulative_population']))
        
        print("RunBasic - final population: %d" % stats['RunBasic']['final_population'])
        print("RunBasic - mean total payoff per round: %.2f" % (1.0 * stats['RunBasic']['total_payoff'] / stats['RunBasic']['N_rounds']))
        


@unittest.skipIf(quickTest, "in quickTest mode")
class TestMovesCumulative(unittest.TestCase):
    
    def setUp(self):
        # Create a new cumulative simulation with the following parameters:
        #   mode_spatial = False
        #   mode_cumulative = True
        #   N_observe = 3
        #   P_copyFail = 0.1
        # The single deme will contain random payoffs for acts.
        
        self.simulation = simulate.Simulate(mode_cumulative = True, P_death = -1.0,  birth_control = True, P_copyFail = 0.0)


    def test_REFINE(self):
        individual = self.simulation.demes[0].population[0]

        commands = ( ( (INNOVATE, ),  ),  )
        self.simulation.step(commands)
        
        learned_act = individual.historyActs[0]
        
        commands = ( ( (EXPLOIT, learned_act),  ),  )
        self.simulation.step(commands)
        
        first_payoff = individual.historyPayoffs[1]

        commands = ( ( (REFINE, learned_act),  ),  )
        self.simulation.step(commands)
        
        second_payoff = individual.historyPayoffs[2]

        commands = ( ( (EXPLOIT, learned_act),  ),  )
        self.simulation.step(commands)
        
        third_payoff = individual.historyPayoffs[3]
        
        self.assertEqual(len(individual.repertoire), 1)
        self.assertEqual(len(individual.historyActs), 4)
        self.assertEqual(len(individual.historyPayoffs), 4)
        
        self.assertListEqual(individual.historyMoves, [INNOVATE, EXPLOIT, REFINE, EXPLOIT])
        self.assertListEqual(individual.historyDemes, [0, 0, 0, 0])
        self.assertListEqual(individual.historyRounds, [1, 2, 3, 4])
        
        self.assertEqual(first_payoff+self.simulation.payoff_increment(1), second_payoff)
        self.assertEqual(first_payoff+self.simulation.payoff_increment(1), third_payoff)
        
    
    def test_REFINE_unknown_act(self):
        """
        Test that attempting to refine an act unknown to the individual raises an exception
        """
        
        individual = self.simulation.demes[0].population[0]

        commands = ( ( (REFINE, 0),  ),  )
        
        with self.assertRaises(KeyError):
            self.simulation.step(commands)
            
    def test_REFINE_then_teach(self):
        """
        Test that an individual observing the exploitation of a refined act, also picks up the refinement
        """
        
        teacher = self.simulation.demes[0].population[0]
        learner = self.simulation.demes[0].population[1]
        
        commands = ( ( (INNOVATE, ), (OBSERVE, ),  ),  )        
        self.simulation.step(commands)
        
        act = teacher.historyActs[0]
        
        commands = ( ( (REFINE, act), (OBSERVE, ),  ),  )        
        self.simulation.step(commands)
        
        commands = ( ( (EXPLOIT, act), (OBSERVE, ),  ),  )        
        self.simulation.step(commands)
        
        self.assertTrue(learner.repertoire.has_key(act))
        self.assertTrue(learner.refinements.has_key(act))
        self.assertEqual(teacher.refinements[act], learner.refinements[act])


@unittest.skipIf(quickTest, "in quickTest mode")
class TestMigrateSpatial(unittest.TestCase):
    
    def setUp(self):
        # Create a new spatial simulation with the following parameters:
        #
        #   mode_spatial = True     - switches on multiple demes and migration
        #   P_death = -1.0          - switches off death
        #   birth_control = True    - switches off births
        #
        # Births and deaths are switched off, so that we know that all units gained or lost to a deme, are due to
        # migration.
        
        self.simulation = simulate.Simulate(mode_spatial = True, P_death = -1.0, birth_control = True)

    def test_Setup(self):
        self.assertEqual(len(self.simulation.demes), 3)
        for d in [0, 1, 2]:
            self.assertEqual(len(self.simulation.demes[d].population), 100)

    def test_Migration(self):
        
        # For the spatial case, we would like to test that the correct number of migrations did happen each turn. This
        # is best achieved through set operations, by checking that individuals lost to one deme are always gained by
        # another deme.
        
        for i in range(0,10):
            
            P_last = {}
            P_new = {}
            P_lost = {}
            P_gained = {}
        
            for d in range(0, self.simulation.N_demes):
                P_last[d] = set(self.simulation.demes[d].population)
            
            self.simulation.step()

            for d in range(0, self.simulation.N_demes):
                P_new[d] = set(self.simulation.demes[d].population)
                P_lost[d] = P_last[d] - P_new[d]
                P_gained[d] = P_new[d] - P_last[d]
                self.assertEqual(len(P_lost[d]), 5)

            for d in range(0, self.simulation.N_demes):
                P_othersGained = set()
                for od in range(0, self.simulation.N_demes):
                    if d != od:
                        P_othersGained = P_othersGained.union(P_gained[od])
                self.assertTrue(P_lost[d].issubset(P_othersGained))
    

@unittest.skipIf(quickTest, "in quickTest mode")
class TestRunSpatial(unittest.TestCase):
    
    def setUp(self):
        # Create a new spatial simulation with the following parameters:
        #   mode_spatial = True
        #   mode_cumulative = False
        #   N_observe = 3
        #   P_copyFail = 0.1
        
        self.simulation = simulate.Simulate(mode_spatial = True)

    def test_Setup(self):
        
        for d in [0,1,2]:
            self.assertEqual(len(self.simulation.demes[d].population), 100)
            self.assertEqual(len(self.simulation.demes[d].acts), 100)

    def test_RunSpatial(self):
        self.simulation.run()
        
        # Verify that all individuals are accounted for (nobody "lost in migration")
        
        final_population = sum([len(self.simulation.demes[d].population) for d in [0, 1, 2]])
        total_births = sum(self.simulation.stat_births.values())
        total_deaths = sum(self.simulation.stat_deaths.values())
        
        self.assertEqual(final_population, 300 + total_births - total_deaths)
        
        total_act_updates = sum([d.stat_act_updates for d in self.simulation.demes])
            
        P_c_accuracy = (1.0 * total_act_updates / self.simulation.N_rounds
                        / simulate.N_ACTS / 3.0 / self.simulation.P_c)
        
        self.assertLess(abs(P_c_accuracy - 1.0), TOLERANCE, 
                        "P_c not simulated to within the required tolerance (%.4f)" % P_c_accuracy)
        
        P_copyFail_accuracy = (1.0 * self.simulation.stat_failed_copies / self.simulation.stat_total_OBSERVEs /
                               self.simulation.P_copyFail)
        
        self.assertLess(abs(P_copyFail_accuracy - 1.0), TOLERANCE, 
                        "P_copyFail not simulated to within the required tolerance")
        
        P_death_accuracy = (1.0 * sum(self.simulation.stat_deaths.values()) 
                               / sum(self.simulation.stat_population.values()) /
                               self.simulation.P_death)
        
        self.assertLess(abs(P_death_accuracy - 1.0), TOLERANCE, 
                               "P_death not simulated to within the required tolerance")

        stats['RunSpatial'] = {}
        stats['RunSpatial']['act_updates'] = total_act_updates
        stats['RunSpatial']['N_rounds'] = self.simulation.N_rounds
        stats['RunSpatial']['P_c'] = self.simulation.P_c
        stats['RunSpatial']['births'] = total_births
        stats['RunSpatial']['deaths'] = total_deaths
        stats['RunSpatial']['P_death'] = self.simulation.P_death
        
        stats['RunSpatial']['cumulative_population']  = sum(self.simulation.stat_population.values())
        stats['RunSpatial']['final_population'] = final_population
        stats['RunSpatial']['total_payoff'] = self.simulation.total_payoff
        stats['RunSpatial']['total_OBSERVEs'] = self.simulation.stat_total_OBSERVEs
        stats['RunSpatial']['failed_copies'] = self.simulation.stat_failed_copies
        stats['RunSpatial']['P_copyFail'] = self.simulation.P_copyFail
        
        # Pickle the simulation object to file, for later analysis and graphing
        f = open('log/test_RunSpatial.sim', 'w')
        pickle.dump(self.simulation, f)
        f.close()


    @staticmethod
    def printReport():

        if (not stats.has_key('RunSpatial')):
            return

        print('--------------------')
        print("RunSpatial - act updates: %d/%d (%.4f) for P_c=%.4f" 
              % (stats['RunSpatial']['act_updates'], stats['RunSpatial']['N_rounds'] * 3 * simulate.N_ACTS, 
                 1.0 * stats['RunSpatial']['act_updates'] / stats['RunSpatial']['N_rounds'] / 3.0
                 / simulate.N_ACTS, 
                 stats['RunSpatial']['P_c']))
    
        print("RunSpatial - failed copies: %d/%d (%.4f) for P_copyFail=%.4f" 
              % (stats['RunSpatial']['failed_copies'], stats['RunSpatial']['total_OBSERVEs'], 
                 1.0 * stats['RunSpatial']['failed_copies'] / stats['RunSpatial']['total_OBSERVEs'], 
                 stats['RunSpatial']['P_copyFail']))

        print("RunSpatial - deaths: %d/%d (%.4f) for P_death=%.4f" 
              % (stats['RunSpatial']['deaths'], stats['RunSpatial']['cumulative_population'], 
                 1.0 * stats['RunSpatial']['deaths'] / stats['RunSpatial']['cumulative_population'], 
                 stats['RunSpatial']['P_death']))
    
        print("RunSpatial - births: %d/%d (%.4f)" 
              % (stats['RunSpatial']['births'], stats['RunSpatial']['cumulative_population'], 
                 1.0 * stats['RunSpatial']['births'] / stats['RunSpatial']['cumulative_population']))
        
        print("RunSpatial - final population: %d" % stats['RunSpatial']['final_population'])
        print("RunSpatial - mean total payoff per round: %.2f" % (1.0 * stats['RunSpatial']['total_payoff'] / stats['RunSpatial']['N_rounds']))


@unittest.skipIf(quickTest, "in quickTest mode")
class TestRunCumulative(unittest.TestCase):
    
    def setUp(self):
        # Create a new spatial simulation with the following parameters:
        #   mode_spatial = False
        #   mode_cumulative = True
        #   N_observe = 3
        #   P_copyFail = 0.1
        # The single deme will contain random payoffs for acts.
        
        self.simulation = simulate.Simulate(mode_cumulative = True)

    def test_RunCumulative(self):
        self.simulation.run()
        
        total_act_updates = sum([d.stat_act_updates for d in self.simulation.demes])
            
        P_c_accuracy = (1.0 * total_act_updates / self.simulation.N_rounds
                        / simulate.N_ACTS / self.simulation.P_c)
        
        self.assertLess(abs(P_c_accuracy - 1.0), TOLERANCE, 
                        "P_c not simulated to within the required tolerance (%.4f)" % P_c_accuracy)
        
        P_copyFail_accuracy = (1.0 * self.simulation.stat_failed_copies / self.simulation.stat_total_OBSERVEs /
                               self.simulation.P_copyFail)
        
        self.assertLess(abs(P_copyFail_accuracy - 1.0), TOLERANCE, 
                        "P_copyFail not simulated to within the required tolerance")
        
        P_death_accuracy = (1.0 * sum(self.simulation.stat_deaths.values()) 
                               / sum(self.simulation.stat_population.values()) /
                               self.simulation.P_death)
        
        self.assertLess(abs(P_death_accuracy - 1.0), TOLERANCE, 
                               "P_death not simulated to within the required tolerance")

        
        final_population = len(self.simulation.demes[0].population)
        total_births = sum(self.simulation.stat_births.values())
        total_deaths = sum(self.simulation.stat_deaths.values())
        
        stats['RunCumulative'] = {}
        stats['RunCumulative']['act_updates'] = self.simulation.demes[0].stat_act_updates
        stats['RunCumulative']['N_rounds'] = self.simulation.N_rounds
        stats['RunCumulative']['P_c'] = self.simulation.P_c
        stats['RunCumulative']['births'] = total_births
        stats['RunCumulative']['deaths'] = total_deaths
        stats['RunCumulative']['P_death'] = self.simulation.P_death
        
        stats['RunCumulative']['cumulative_population']  = sum(self.simulation.stat_population.values())
        stats['RunCumulative']['final_population'] = final_population
        stats['RunCumulative']['total_payoff'] = self.simulation.total_payoff
        stats['RunCumulative']['total_OBSERVEs'] = self.simulation.stat_total_OBSERVEs
        stats['RunCumulative']['failed_copies'] = self.simulation.stat_failed_copies
        stats['RunCumulative']['P_copyFail'] = self.simulation.P_copyFail
        
        # Pickle the simulation object to file, for later analysis and graphing
        f = open('log/test_RunCumulative.sim', 'w')
        pickle.dump(self.simulation, f)
        f.close()


    @staticmethod
    def printReport():

        if (not stats.has_key('RunCumulative')):
            return

        print('--------------------')
        print("RunCumulative - act updates: %d/%d (%.4f) for P_c=%.4f" 
              % (stats['RunCumulative']['act_updates'], stats['RunCumulative']['N_rounds'] * simulate.N_ACTS, 
                 1.0 * stats['RunCumulative']['act_updates'] / stats['RunCumulative']['N_rounds']
                 / simulate.N_ACTS, 
                 stats['RunCumulative']['P_c']))
    
        print("RunCumulative - failed copies: %d/%d (%.4f) for P_copyFail=%.4f" 
              % (stats['RunCumulative']['failed_copies'], stats['RunCumulative']['total_OBSERVEs'], 
                 1.0 * stats['RunCumulative']['failed_copies'] / stats['RunCumulative']['total_OBSERVEs'], 
                 stats['RunCumulative']['P_copyFail']))

        print("RunCumulative - deaths: %d/%d (%.4f) for P_death=%.4f" 
              % (stats['RunCumulative']['deaths'], stats['RunCumulative']['cumulative_population'], 
                 1.0 * stats['RunCumulative']['deaths'] / stats['RunCumulative']['cumulative_population'], 
                 stats['RunCumulative']['P_death']))
    
        print("RunCumulative - births: %d/%d (%.4f)" 
              % (stats['RunCumulative']['births'], stats['RunCumulative']['cumulative_population'], 
                 1.0 * stats['RunCumulative']['births'] / stats['RunCumulative']['cumulative_population']))
        
        print("RunCumulative - final population: %d" % stats['RunCumulative']['final_population'])
        print("RunCumulative - mean total payoff per round: %.2f" % (1.0 * stats['RunCumulative']['total_payoff'] / stats['RunCumulative']['N_rounds']))


@unittest.skipIf(quickTest, "in quickTest mode")
class TestRunMax(unittest.TestCase):
    
    def setUp(self):
        # Create a new spatial simulation with the following parameters:
        #   mode_spatial = True
        #   mode_cumulative = True
        #   N_observe = 10
        #   P_copyFail = 0.5
        #   P_c = 0.4
        #   N_migrate = 20
        #   r_max = 1000
        # The single deme will contain random payoffs for acts.
        
        self.simulation = simulate.Simulate(mode_spatial = True,
                                            mode_cumulative = True,
                                            N_observe = 10,
                                            P_copyFail = 0.5,
                                            P_c = 0.4,
                                            N_migrate = 20,
                                            r_max = 1000)

    def test_RunMax(self):
        self.simulation.run()
        
        total_act_updates = sum([d.stat_act_updates for d in self.simulation.demes])
            
        P_c_accuracy = (1.0 * total_act_updates / self.simulation.N_rounds
                        / simulate.N_ACTS / 3.0 / self.simulation.P_c)
        
        self.assertLess(abs(P_c_accuracy - 1.0), TOLERANCE, 
                        "P_c not simulated to within the required tolerance (%.4f)" % P_c_accuracy)
        
        P_copyFail_accuracy = (1.0 * self.simulation.stat_failed_copies / self.simulation.stat_total_OBSERVEs /
                               self.simulation.P_copyFail)
        
        self.assertLess(abs(P_copyFail_accuracy - 1.0), TOLERANCE, 
                        "P_copyFail not simulated to within the required tolerance")
        
        P_death_accuracy = (1.0 * sum(self.simulation.stat_deaths.values()) 
                               / sum(self.simulation.stat_population.values()) /
                               self.simulation.P_death)
        
        self.assertLess(abs(P_death_accuracy - 1.0), TOLERANCE, 
                               "P_death not simulated to within the required tolerance")
        
        final_population = sum([len(self.simulation.demes[d].population) for d in [0, 1, 2]])
        total_births = sum(self.simulation.stat_births.values())
        total_deaths = sum(self.simulation.stat_deaths.values())
        
        stats['RunMax'] = {}
        stats['RunMax']['act_updates'] = total_act_updates
        stats['RunMax']['N_rounds'] = self.simulation.N_rounds
        stats['RunMax']['P_c'] = self.simulation.P_c     
        stats['RunMax']['births'] = total_births
        stats['RunMax']['deaths'] = total_deaths
        stats['RunMax']['P_death'] = self.simulation.P_death
        
        stats['RunMax']['cumulative_population']  = sum(self.simulation.stat_population.values())
        stats['RunMax']['final_population'] = final_population
        stats['RunMax']['total_payoff'] = self.simulation.total_payoff
        stats['RunMax']['total_OBSERVEs'] = self.simulation.stat_total_OBSERVEs
        stats['RunMax']['failed_copies'] = self.simulation.stat_failed_copies
        stats['RunMax']['P_copyFail'] = self.simulation.P_copyFail
        
        # Pickle the simulation object to file, for later analysis and graphing
        f = open('log/test_RunMax.sim', 'w')
        pickle.dump(self.simulation, f)
        f.close()
    
    
    @staticmethod
    def printReport():

        if (not stats.has_key('RunMax')):
            return

        print('--------------------')
        print("RunMax - act updates: %d/%d (%.4f) for P_c=%.4f" 
              % (stats['RunMax']['act_updates'], stats['RunMax']['N_rounds'] * simulate.N_ACTS * 3, 
                 1.0 * stats['RunMax']['act_updates'] / stats['RunMax']['N_rounds']
                 / simulate.N_ACTS / 3.0, 
                 stats['RunMax']['P_c']))
    
        print("RunMax - failed copies: %d/%d (%.4f) for P_copyFail=%.4f" 
              % (stats['RunMax']['failed_copies'], stats['RunMax']['total_OBSERVEs'], 
                 1.0 * stats['RunMax']['failed_copies'] / stats['RunMax']['total_OBSERVEs'], 
                 stats['RunMax']['P_copyFail']))

        print("RunMax - deaths: %d/%d (%.4f) for P_death=%.4f" 
              % (stats['RunMax']['deaths'], stats['RunMax']['cumulative_population'], 
                 1.0 * stats['RunMax']['deaths'] / stats['RunMax']['cumulative_population'], 
                 stats['RunMax']['P_death']))
    
        print("RunMax - births: %d/%d (%.4f)" 
              % (stats['RunMax']['births'], stats['RunMax']['cumulative_population'], 
                 1.0 * stats['RunMax']['births'] / stats['RunMax']['cumulative_population']))
        
        print("RunMax - final population: %d" % stats['RunMax']['final_population'])
        print("RunMax - mean total payoff per round: %.2f" % (1.0 * stats['RunMax']['total_payoff'] / stats['RunMax']['N_rounds']))


@unittest.skipIf(quickTest, "in quickTest mode")
class TestModelBias(unittest.TestCase):
    
    def setUp(self):
        # Create a new simulation in model_bias mode:
        
        self.simulation = simulate.Simulate(N_rounds = 100, P_death = -1.0,  birth_control = True,
                                            mode_model_bias = True,  P_copyFail = -1.0)
        agent.OBSERVE_STRATEGY = 'unittest'
        

    def test_OBSERVE_N(self):
        self.simulation.N_observe = 5
        
        teachers = self.simulation.demes[0].population[0:99]
        learner = self.simulation.demes[0].population[99]

        commands = ( ( ( (INNOVATE, ), ) * 100 ),  )
        self.simulation.step(commands)
        
        teacher_acts = [t.historyActs[0] for t in teachers]
        
        commands = (tuple( [ (EXPLOIT,  teacher_acts[x]) for x in range(0, 99) ] )
                    + ((OBSERVE, ), ), )
        
        self.simulation.step(commands)
        
        preferred_teachers = range(0, 99)
        random.shuffle(preferred_teachers, lambda: 0)
        
        preferred_acts = [teachers[preferred_teachers[x]].historyActs[0] for x in range(0, self.simulation.N_observe)]
        preferred_acts.sort()
        
        learned_acts = learner.historyActs[1:(self.simulation.N_observe+1)]
        learned_acts.sort()
        
        self.assertListEqual(preferred_acts, learned_acts)


@unittest.skipIf(quickTest, "in quickTest mode")
class TestRepeatability(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def test_Repeatability(self):
        
        sim1 = simulate.Simulate(N_rounds = 1000,
                                 mode_model_bias = True,
                                 mode_cumulative = True,
                                 mode_spatial = True,
                                 seed = 'test_Repeatability')
        
        sim1.run()
        
        sim2 = simulate.Simulate(N_rounds = 1000,
                                 mode_model_bias = True,
                                 mode_cumulative = True,
                                 mode_spatial = True,
                                 seed = 'test_Repeatability')
        
        # Kick the local random number generator, to verify that it has no effect on the
        # simulation's state.
        random.jumpahead(1)
        
        sim2.run()
        
        pop1 = sim1.demes[0].population + \
               sim1.demes[1].population + \
               sim1.demes[2].population
        pop2 = sim2.demes[0].population + \
               sim2.demes[1].population + \
               sim2.demes[2].population
        
        self.assertEqual(len(pop1), len(pop2))
        
        for i in xrange(0, len(pop1)):
            self.assertListEqual(pop1[i].historyRounds, pop2[i].historyRounds)
            self.assertListEqual(pop1[i].historyMoves, pop2[i].historyMoves)
            self.assertListEqual(pop1[i].historyActs, pop2[i].historyActs)
            self.assertListEqual(pop1[i].historyPayoffs, pop2[i].historyPayoffs)
            self.assertListEqual(pop1[i].historyDemes, pop2[i].historyDemes)


def tearDownModule():
    print("\n\nSTATISTICS")
    TestRunBasic.printReport()
    TestRunSpatial.printReport()
    TestRunCumulative.printReport()
    TestRunMax.printReport()

if __name__ == '__main__':
    stats = {}
    SEED = 'zeta'
    random.seed(SEED)
    print("Running unit tests... (random seed: %s)" % SEED)
    unittest.main()
