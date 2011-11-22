import fitness
import repodata
import random

if __name__ == '__main__':
    
    # We only explore agents that have been submitted to the local git repository
    repo = repodata.RepoData()
    
    while True:
        
        # This returns a git blob corresponding to the desired agent
        agent = random.choice(repo.agents_fitness)
        
        print agent.name
        
        input()
        
