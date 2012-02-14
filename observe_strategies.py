# This function MUST return the given list of tuples, exploiterData, sorted by preference for copying.
# Data given for each agent are (index in this list,age,total accrued payoff,number of times copied,number of offpsring)
# All values except index have error applied.

# AGE = 1
# TOTAL_PAY = 2
# TIMES_COPIED = 3
# N_OFFSPRING = 4

strategy = [
"    return sorted(exploiterData,key=lambda x:x[AGE],reverse=True)\n",
"    return sorted(exploiterData,key=lambda x:x[TOTAL_PAY],reverse=True)\n",
"    return sorted(exploiterData,key=lambda x:x[TIMES_COPIED],reverse=True)\n",
"    return sorted(exploiterData,key=lambda x:x[N_OFFSPRING],reverse=True)\n",
"    random.shuffle(exploiterData)\n    return exploiterData\n"
]

