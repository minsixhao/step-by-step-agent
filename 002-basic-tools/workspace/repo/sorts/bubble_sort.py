from typing import Any


def bubble_sort_iterative(collection: list[Any]) -> list[Any]:
    """Pure implementation of bubble sort algorithm in Python

    :param collection: some mutable ordered collection with heterogeneous
    comparable items inside
    :return: the same collection ordered in descending order

    Examples:
    >>> bubble_sort_iterative([0, 5, 2, 3, 2])
    [5, 3, 2, 2, 0]
    >>> bubble_sort_iterative([])
    []
    >>> bubble_sort_iterative([-2, -45, -5])
    [-2, -5, -45]
    >>> bubble_sort_iterative([-23, 0, 6, -4, 34])
    [34, 6, 0, -4, -23]
    >>> bubble_sort_iterative([1, 2, 3, 4])
    [4, 3, 2, 1]
    >>> bubble_sort_iterative([3, 3, 3, 3])
    [3, 3, 3, 3]
    >>> bubble_sort_iterative([56])
    [56]
    >>> bubble_sort_iterative([0, 5, 2, 3, 2]) == sorted([0, 5, 2, 3, 2], reverse=True)
    True
    >>> bubble_sort_iterative([]) == sorted([], reverse=True)
    True
    >>> bubble_sort_iterative([-2, -45, -5]) == sorted([-2, -45, -5], reverse=True)
    True
    >>> bubble_sort_iterative([-23, 0, 6, -4, 34]) == sorted([-23, 0, 6, -4, 34], reverse=True)
    True
    >>> bubble_sort_iterative(['d', 'a', 'b', 'e']) == sorted(['d', 'a', 'b', 'e'], reverse=True)
    True
    >>> bubble_sort_iterative(['z', 'a', 'y', 'b', 'x', 'c'])
    ['z', 'y', 'x', 'c', 'b', 'a']
    >>> bubble_sort_iterative([1.1, 3.3, 5.5, 7.7, 2.2, 4.4, 6.6])
    [7.7, 6.6, 5.5, 4.4, 3.3, 2.2, 1.1]
    >>> bubble_sort_iterative([1, 3.3, 5, 7.7, 2, 4.4, 6])
    [7.7, 6, 5, 4.4, 3.3, 2, 1]
    >>> import random
    >>> collection_arg = random.sample(range(-50, 50), 100)
    >>> bubble_sort_iterative(collection_arg) == sorted(collection_arg, reverse=True)
    True
    >>> import string
    >>> collection_arg = random.choices(string.ascii_letters + string.digits, k=100)
    >>> bubble_sort_iterative(collection_arg) == sorted(collection_arg, reverse=True)
    True
    """
    length = len(collection)
    for i in reversed(range(length)):
        swapped = False
        for j in range(i):
            if collection[j] < collection[j + 1]:
                swapped = True
                collection[j], collection[j + 1] = collection[j + 1], collection[j]
        if not swapped:
            break  # Stop iteration if the collection is sorted.
    return collection


def bubble_sort_recursive(collection: list[Any]) -> list[Any]:
    """It is similar iterative bubble sort but recursive.

    :param collection: mutable ordered sequence of elements
    :return: the same list in descending order

    Examples:
    >>> bubble_sort_recursive([0, 5, 2, 3, 2])
    [5, 3, 2, 2, 0]
    >>> bubble_sort_recursive([])
    []
    >>> bubble_sort_recursive([-2, -45, -5])
    [-2, -5, -45]
    >>> bubble_sort_recursive([-23, 0, 6, -4, 34])
    [34, 6, 0, -4, -23]
    >>> bubble_sort_recursive([0, 5, 2, 3, 2]) == sorted([0, 5, 2, 3, 2], reverse=True)
    True
    >>> bubble_sort_recursive([]) == sorted([], reverse=True)
    True
    >>> bubble_sort_recursive([-2, -45, -5]) == sorted([-2, -45, -5], reverse=True)
    True
    >>> bubble_sort_recursive([-23, 0, 6, -4, 34]) == sorted([-23, 0, 6, -4, 34], reverse=True)
    True
    >>> bubble_sort_recursive(['d', 'a', 'b', 'e']) == sorted(['d', 'a', 'b', 'e'], reverse=True)
    True
    >>> bubble_sort_recursive(['z', 'a', 'y', 'b', 'x', 'c'])
    ['z', 'y', 'x', 'c', 'b', 'a']
    >>> bubble_sort_recursive([1.1, 3.3, 5.5, 7.7, 2.2, 4.4, 6.6])
    [7.7, 6.6, 5.5, 4.4, 3.3, 2.2, 1.1]
    >>> bubble_sort_recursive([1, 3.3, 5, 7.7, 2, 4.4, 6])
    [7.7, 6, 5, 4.4, 3.3, 2, 1]
    >>> bubble_sort_recursive(['a', 'Z', 'B', 'C', 'A', 'c'])
    ['c', 'a', 'Z', 'C', 'B', 'A']
    >>> import random
    >>> collection_arg = random.sample(range(-50, 50), 100)
    >>> bubble_sort_recursive(collection_arg) == sorted(collection_arg, reverse=True)
    True
    >>> import string
    >>> collection_arg = random.choices(string.ascii_letters + string.digits, k=100)
    >>> bubble_sort_recursive(collection_arg) == sorted(collection_arg, reverse=True)
    True
    """
    length = len(collection)
    swapped = False
    for i in range(length - 1):
        if collection[i] < collection[i + 1]:
            collection[i], collection[i + 1] = collection[i + 1], collection[i]
            swapped = True

    return collection if not swapped else bubble_sort_recursive(collection)


if __name__ == "__main__":
    import doctest
    from random import sample
    from timeit import timeit

    doctest.testmod()

    # Benchmark: Iterative seems slightly faster than recursive.
    num_runs = 10_000
    unsorted = sample(range(-50, 50), 100)
    timer_iterative = timeit(
        "bubble_sort_iterative(unsorted[:])", globals=globals(), number=num_runs
    )
    print("\nIterative bubble sort:")
    print(*bubble_sort_iterative(unsorted), sep=",")
    print(f"Processing time (iterative): {timer_iterative:.5f}s for {num_runs:,} runs")

    unsorted = sample(range(-50, 50), 100)
    timer_recursive = timeit(
        "bubble_sort_recursive(unsorted[:])", globals=globals(), number=num_runs
    )
    print("\nRecursive bubble sort:")
    print(*bubble_sort_recursive(unsorted), sep=",")
    print(f"Processing time (recursive): {timer_recursive:.5f}s for {num_runs:,} runs")
