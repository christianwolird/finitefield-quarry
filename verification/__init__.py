"""Utilities for checking the repository's recorded search results.

These scripts check that all recorded solutions are valid and that there is
a record for each prime and prime power beneath the bound. The only thing
these scripts don't do is verify the negative results (e.g. that the fields
marked as having no solution really don't have any solution). This negative
verification essentially requires re-running the search algorithms entirely.
"""
