"""
This module contains some examplary state graphs, that are likely to give good initial results when
simulated. These are intended to be used to seed the initial genetic programming population.
"""

import traits

def BifurcateDiscrete():

	self_traits = {}

	self_traits['PioneeringBi'] = traits.PioneeringBi.PioneeringBi()
	self_traits['PioneeringBi'].N_rounds = 3

	self_traits['Specialisation'] = traits.Specialisation.Specialisation()
	self_traits['SpecialisationB'] = traits.SpecialisationB.SpecialisationB()

	self_traits['DiscreteDistribution'] = traits.DiscreteDistribution.DiscreteDistribution()
	self_traits['DiscreteDistributionB'] = traits.DiscreteDistributionB.DiscreteDistributionB()
	self_traits['DiscreteDistributionC'] = traits.DiscreteDistributionC.DiscreteDistributionC()
	self_traits['DiscreteDistributionD'] = traits.DiscreteDistributionD.DiscreteDistributionD()
	self_traits['DiscreteDistributionE'] = traits.DiscreteDistributionE.DiscreteDistributionE()
	self_traits['DiscreteDistributionF'] = traits.DiscreteDistributionF.DiscreteDistributionF()
	self_traits['DiscreteDistributionG'] = traits.DiscreteDistributionG.DiscreteDistributionG()
	self_traits['DiscreteDistributionH'] = traits.DiscreteDistributionH.DiscreteDistributionH()

	state = [('PioneeringBi', ['Specialisation', 'SpecialisationB']),
	         ('Specialisation', ['DiscreteDistribution','DiscreteDistributionB','DiscreteDistributionC','DiscreteDistributionD']),
	         ('SpecialisationB', ['DiscreteDistributionE','DiscreteDistributionF','DiscreteDistributionG','DiscreteDistributionH']),
	         ('DiscreteDistribution', []),
	         ('DiscreteDistributionB', []),
	         ('DiscreteDistributionC', []),
	         ('DiscreteDistributionD', []),
	         ('DiscreteDistributionE', []),
	         ('DiscreteDistributionF', []),
	         ('DiscreteDistributionG', []),
	         ('DiscreteDistributionH', []),
	        ]
	
	return (self_traits, state)


def Simple():

	self_traits = {}

	self_traits['Pioneering'] = traits.Pioneering.Pioneering()
	self_traits['DiscreteDistribution'] = traits.DiscreteDistribution.DiscreteDistribution()

	state = [('Pioneering', ['DiscreteDistribution']),
		     ('DiscreteDistribution', [])
		    ]

	return (self_traits, state)


def SpecialPioneers():

	self_traits = {}

	self_traits['PioneeringBi'] = traits.Pioneering.Pioneering()
	self_traits['DiscreteDistribution'] = traits.DiscreteDistribution.DiscreteDistribution()
	self_traits['DiscreteDistributionB'] = traits.DiscreteDistributionB.DiscreteDistributionB()

	state = [('PioneeringBi', ['DiscreteDistribution', 'DiscreteDistributionB']),
		     ('DiscreteDistribution', []),
		     ('DiscreteDistributionB', [])
		    ]
		    
	return (self_traits, state)


exemplar_list = [BifurcateDiscrete, Simple, SpecialPioneers]
