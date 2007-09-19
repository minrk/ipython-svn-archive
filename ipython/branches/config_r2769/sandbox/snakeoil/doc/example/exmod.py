"""Simple example module.

This module simply defines a few functions with docstrings and doctests in
them.  It will be tested as part of the integrated test suite later."""

def add(x,y):
    """Add x and y

    :Examples:
        >>> add(1,2)
        3

        >>> add('Hello',' world')
        'Hello world'

        >>> add([1,2],[3,4])
        [1, 2, 3, 4]
    """
    return x+y


def qsort(lst):
    """Return a sorted copy of the input list.

    Taken from the Python Cookbook, due to Nathan Gray.

    :Examples:
        >>> qsort([])
        []

        >>> qsort([1])
        [1]

        >>> qsort([1,2,3,4])
        [1, 2, 3, 4]

        >>> qsort([3,2,1,4])
        [1, 2, 3, 4]
    """

    if len(lst) <= 1:
        return lst

    # Select pivot and apply recursively
    pivot, rest   = lst[0],lst[1:]
    less_than     = [ lt for lt in rest if lt < pivot ]
    greater_equal = [ ge for ge in rest if ge >= pivot ]

    return qsort(less_than) + [pivot] + qsort(greater_equal)
