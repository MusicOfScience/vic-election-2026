"""Compare frozen simulation JSON across platforms at machine precision.

Schema, text, flags and integer counts are exact. Float absolute tolerance is
1e-12, far below one 1/5000 simulation increment or displayed vote precision.
This does not compare or loosen any statistical production-promotion gate.
"""
import json
import math
import sys

def compare(expected, actual, path='$'):
    if isinstance(expected, bool) or expected is None or isinstance(expected, str):
        if type(expected) is not type(actual) or expected != actual:
            raise AssertionError(f'{path}: exact value mismatch {expected!r} vs {actual!r}')
        return 0.0
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or expected.keys() != actual.keys():
            raise AssertionError(f'{path}: schema keys differ')
        return max((compare(v,actual[k],f'{path}.{k}') for k,v in expected.items()),default=0.0)
    if isinstance(expected, list):
        if not isinstance(actual,list) or len(expected)!=len(actual):
            raise AssertionError(f'{path}: array length differs')
        return max((compare(v,actual[i],f'{path}[{i}]') for i,v in enumerate(expected)),default=0.0)
    if isinstance(expected, int):
        if type(actual) is not int or expected != actual:
            raise AssertionError(f'{path}: integer count differs')
        return 0.0
    if type(expected) is not float or type(actual) is not float or not math.isfinite(expected) or not math.isfinite(actual):
        raise AssertionError(f'{path}: numeric type or finiteness mismatch')
    difference=abs(expected-actual)
    if difference>1e-12:
        raise AssertionError(f'{path}: {expected!r} vs {actual!r}, difference={difference}')
    return difference

if __name__=='__main__':
    difference=compare(json.load(open(sys.argv[1])),json.load(open(sys.argv[2])))
    print(f'Campaign JSON matches; maximum absolute float difference {difference:.3g}; exact schema/text/counts.')
