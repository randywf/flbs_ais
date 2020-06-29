# -*- coding: utf-8 -*-

import pytest
from flbs_ais.skeleton import fib

__author__ = "Randy Flores"
__copyright__ = "Randy Flores"
__license__ = "mit"


def test_fib():
    assert fib(1) == 1
    assert fib(2) == 1
    assert fib(7) == 13
    with pytest.raises(AssertionError):
        fib(-10)
