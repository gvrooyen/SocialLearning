"""
Timer class that measures the total running time of code, over numerous invocations.

Based on an example by Corey Porter on Stack Overflow:
http://stackoverflow.com/questions/1685221/accurately-measure-time-python-function-takes

Usage example:

>>> timer = Timer()
>>> with timer:
>>>     foo()
>>>     bar()
>>> print timer.total_time()
>>> print timer.N_calls()
>>> print timer.avg_time()

"""

import time

class Timer(object):
    
    def __init__(self):
        self._N_calls = 0
        self._total_time = 0.0
    
    def __enter__(self):
        self._N_calls += 1
        self._start = time.time()
    
    def __exit__(self, type, value, traceback):
        self._finish = time.time()
        self._total_time += self._finish - self._start
    
    def total_time(self):
        return self._total_time
    
    def N_calls(self):
        return self._N_calls
    
    def avg_time(self):
        return self._total_time / self._N_calls
