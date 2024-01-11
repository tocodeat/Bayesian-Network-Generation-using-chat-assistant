import pytest
from typing import Tuple, Dict, List

import pandas as pd
from app.src.cpm import CPMCalculator

@pytest.fixture(params=[
    # Test case 1
    ({
        'a': [],
        'b': ['a'],
        'c': ['a'],
        'd': ['b'],
        'e': ['c', 'd']
    },
    {
        'a': 5,
        'b': 4,
        'c': 10,
        'd': 2,
        'e': 5
    }),
    
    # Test case 2
    ({
        'a': [],
        'b': ['a'],
        'c': ['a'],
        'd': ['b'],
        'e': ['c', 'd'],
        'f': ['e'],
        'g': ['e']
    },
    {
        'a': 5,
        'b': 4,
        'c': 10,
        'd': 2,
        'e': 5,
        'f': 3,
        'g': 6
    }),
    
    # Test case 3
    ({
        'a': [],
        'b': ['a'],
        'c': ['a'],
        'd': ['b'],
        'e': ['c', 'd'],
        'f': ['e'],
        'g': ['e']
    },
    {
        'a': 5,
        'b': 4,
        'c': 10,
        'd': 2,
        'e': 5,
        'f': 3,
        'g': 6
    }),
    
    # Test 4
    ({
        'a': [],
        'b': ['a'],
        'c': ['a'],
        'd': ['b'],
        'e': ['c', 'd']
    },
    {
        'a': 5,
        'b': 4,
        'c': 10,
        'd': 2,
        'e': 5
    }),
    
    # Test 5
    ({
        'a': [],
        'b': ['a'],
        'c': ['a'],
        'd': ['b', 'c'],
        'e': ['d'],
        'f': [],
        'g': ['f'],
        'h': ['f', 'e']
    },
    {
        'a': 3,
        'b': 5,
        'c': 2,
        'd': 4,
        'e': 6,
        'f': 7,
        'g': 3,
        'h': 5
    })
])
def cpm_data(request) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    return request.param

class TestCPMCalculator:
    """
    Test class for CPMCalculator (numpy implementation) against old implementation.
    """
    def test_cpm_calculator(self, cpm_data):
        activities, durations = cpm_data
        
        cpm = CPMCalculator(activities, durations)

        
        result = cpm.get_results()