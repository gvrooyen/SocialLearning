import fitness
import repodata
import random
import ranges

from math import exp, log

def selectParameters(agent_name, explore_ranges):
    """
    Return a set of simulation parameters for the specified agent's next fitness exploration run.
    
    Currently, the parameters are just uniform random samples from the specified ranges. Cleverer algorithms are
    possible, e.g. by exploring sparsely sampled regions, or by giving greater preference to "interesting" regions
    where one or more partial derivatives are high.
    
    For now we explore the agent_name parameter. It will become useful once we need to do database lookups to determine
    "good" regions to explore.
    """
    
    result = {}
    
    for key, value in explore_ranges.iteritems():
        
        if value[0] == bool:
            if value[1] == None:
                result[key] = random.choice((True, False))
            else:
                result[key] = value[2]
                
        elif value[0] == int:
            result[key] = random.randint(value[1], value[2])
            
        elif value[0] == float:
            if (value[1] > 0.0) and (value[2] > 0.0) and (value[2]/value[1] > 100.0):
                # For a range specification like (float, 0.001, 0.4), rather sample on an log-range
                result[key] = exp(random.uniform(log(value[1]), log(value[2])))
            else:
                # For a range specification like (float, 0.0, 0.5), sample on a uniform range
                result[key] = random.uniform(value[1], value[2])
        
        else:
            raise ValueError("Unsupported range specification: %s" % value[0])
    
    return result
        

if __name__ == '__main__':
    
    # We only explore agents that have been submitted to the local git repository
    repo = repodata.RepoData()
    
    while True:
        
        # This returns a git blob corresponding to the desired agent. Useful fields are agent.name (the filename) and
        # agent.path (filename including relative path)
        agent_repo = random.choice(repo.agents_fitness)
        
        # Convert the agent's path from something like 'agents/fitness/Reference.py' to an importable submodule
        # path like 'agents.fitness.Reference'
        agent_module_name = agent_repo.path.replace('/', '.')[:-3]
        
        # Do an import by string reference. The 'fromlist' argument is necessary because we are importing a submodule
        # from a package (otherwise only the empty 'fitness' module will be imported        
        agent = __import__(agent_module_name, fromlist=['*'])
        
        try:
            explore_ranges = agent.explore_ranges
        except AttributeError:
            explore_ranges = ranges.ParameterRange
        
        params = selectParameters(agent_repo.name, explore_ranges)
        
        sample = fitness.fitness(agent_module_name, params, 1000, 20)
        
        print("-----")
        print(agent.__name__)
        print(params)
        print("FITNESS: %d" % sample.avg_payoff)

