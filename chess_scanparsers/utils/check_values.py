"""Functions to help check that user-supplied values are of a certain
type, or have a certain value, etc.
"""

from logging import getLogger
from typing import Union

import numpy as np

logger = getLogger(__name__)

Int = Union[int, np.integer]
Float = Union[float, np.floating]
Num = Union[int, np.integer, float, np.floating]


def is_int(
        value, ge=None, gt=None, le=None, lt=None, raise_error=False,
        log=True):
    """Value is an integer in range ge <= value <= le or
    gt < value < lt or some combination.

    :param value: Input value.
    :type value: int
    :param ge: Greater or equal to.
    :type ge: int, optional
    :param gt: Greater than.
    :type gt: int, optional
    :param le: Smaller or equal to.
    :type le: int, optional
    :param lt: Smaller than.
    :type lt: int, optional
    :param raise_error: Raise an error, defaults to `False`.
    :type raise_error: bool, optional
    :param log: Write error message to the logger, defaults to `True`.
    :type log: bool, optional
    :return: `True` if input value is in valid range or `False` if not.
    :rtype: bool
    """
    return _is_int_or_num(value, 'int', ge, gt, le, lt, raise_error, log)


def is_num(
        value, ge=None, gt=None, le=None, lt=None, raise_error=False,
        log=True):
    """Value is a number in range ge <= value <= le or gt < value < lt
    or some combination.

    :param value: Input value.
    :type value: int or float
    :param ge: Greater or equal to.
    :type ge: int or float, optional
    :param gt: Greater than.
    :type gt: int or float, optional
    :param le: Smaller or equal to.
    :type le: int or float, optional
    :param lt: Smaller than.
    :type lt: int or float, optional
    :param raise_error: Raise an error, defaults to `False`.
    :type raise_error: bool, optional
    :param log: Write error message to the logger, defaults to `True`.
    :type log: bool, optional
    :return: `True` if input value is in valid range or `False` if not.
    :rtype: bool
    """
    return _is_int_or_num(value, 'num', ge, gt, le, lt, raise_error, log)


def is_int_series(
        t_or_l, ge=None, gt=None, le=None, lt=None, raise_error=False,
        log=True):
    """Value is a tuple or list of integers, each in range
    ge <= l[i] <= le or gt < l[i] < lt or some combination.

    :param t_or_l: Input values.
    :type t_or_l: list[int]
    :param ge: Greater or equal to.
    :type ge: int, optional
    :param gt: Greater than.
    :type gt: int, optional
    :param le: Smaller or equal to.
    :type le: int, optional
    :param lt: Smaller than.
    :type lt: int, optional
    :param raise_error: Raise an error, defaults to `False`.
    :type raise_error: bool, optional
    :param log: Write error message to the logger, defaults to `True`.
    :type log: bool, optional
    :return: `True` if input value is a valid list or `False` if not.
    :rtype: bool
    """
    if not test_ge_gt_le_lt(
            ge, gt, le, lt, is_int, 'is_int_series', raise_error, log):
        return False
    if not isinstance(t_or_l, (tuple, list)):
        illegal_value(t_or_l, 't_or_l', 'is_int_series', raise_error, log)
        return False
    if any(not is_int(v, ge, gt, le, lt, raise_error, log) for v in t_or_l):
        return False
    return True


def _is_int_or_num(
        value, type_str, ge=None, gt=None, le=None, lt=None, raise_error=False,
        log=True):
    if type_str == 'int':
        if not isinstance(value, Int):
            illegal_value(value, 'value', '_is_int_or_num', raise_error, log)
            return False
        if not test_ge_gt_le_lt(
                ge, gt, le, lt, is_int, '_is_int_or_num', raise_error, log):
            return False
    elif type_str == 'num':
        if not isinstance(value, Num):
            illegal_value(value, 'value', '_is_int_or_num', raise_error, log)
            return False
        if not test_ge_gt_le_lt(
                ge, gt, le, lt, is_num, '_is_int_or_num', raise_error, log):
            return False
    else:
        illegal_value(type_str, 'type_str', '_is_int_or_num', raise_error, log)
        return False
    if ge is None and gt is None and le is None and lt is None:
        return True
    error = False
    error_msg = ''
    if ge is not None and value < ge:
        error = True
        error_msg = f'Value {value} out of range: {value} !>= {ge}'
    if not error and gt is not None and value <= gt:
        error = True
        error_msg = f'Value {value} out of range: {value} !> {gt}'
    if not error and le is not None and value > le:
        error = True
        error_msg = f'Value {value} out of range: {value} !<= {le}'
    if not error and lt is not None and value >= lt:
        error = True
        error_msg = f'Value {value} out of range: {value} !< {lt}'
    if error:
        if log:
            logger.error(error_msg)
        if raise_error:
            raise ValueError(error_msg)
        return False
    return True


def is_str_series(t_or_l, raise_error=False, log=True):
    """Value is a tuple or list of strings.

    :param t_or_l: Input values.
    :type t_or_l: tuple[str] or list[str]
    :param raise_error: Raise an error, defaults to `False`.
    :type raise_error: bool, optional
    :param log: Write error message to the logger, defaults to `True`.
    :type log: bool, optional
    :return: `True` if input value is a valid `False` if not.
    :rtype: bool
    """
    if (not isinstance(t_or_l, (tuple, list))
            or any(not isinstance(s, str) for s in t_or_l)):
        illegal_value(t_or_l, 't_or_l', 'is_str_series', raise_error, log)
        return False
    return True


def test_ge_gt_le_lt(
        ge, gt, le, lt, func, location=None, raise_error=False, log=True):
    """Check individual and mutual validity of ge, gt, le, lt
    qualifiers.

    :param ge: Greater or equal to.
    :type ge: int or float
    :param gt: Greater than.
    :type gt: int or float
    :param le: Smaller or equal to.
    :type le: int or float
    :param lt: Smaller than.
    :type lt: int or float
    :param func: Test for integers or numbers.
    :type func: callable: is_int, is_num
    :param location: Input location.
    :type location: str, optional
    :param raise_error: Raise an error, defaults to `False`.
    :type raise_error: bool, optional
    :param log: Write error message to the logger, defaults to `True`.
    :type log: bool, optional
    :return: `True` upon success or `False` when mutually exlusive.
    :rtype: bool
    """
    if ge is None and gt is None and le is None and lt is None:
        return True
    if ge is not None:
        if not func(ge):
            illegal_value(ge, 'ge', location, raise_error, log)
            return False
        if gt is not None:
            illegal_combination(ge, 'ge', gt, 'gt', location, raise_error, log)
            return False
    elif gt is not None and not func(gt):
        illegal_value(gt, 'gt', location, raise_error, log)
        return False
    if le is not None:
        if not func(le):
            illegal_value(le, 'le', location, raise_error, log)
            return False
        if lt is not None:
            illegal_combination(le, 'le', lt, 'lt', location, raise_error, log)
            return False
    elif lt is not None and not func(lt):
        illegal_value(lt, 'lt', location, raise_error, log)
        return False
    if ge is not None:
        if le is not None and ge > le:
            illegal_combination(ge, 'ge', le, 'le', location, raise_error, log)
            return False
        if lt is not None and ge >= lt:
            illegal_combination(ge, 'ge', lt, 'lt', location, raise_error, log)
            return False
    elif gt is not None:
        if le is not None and gt >= le:
            illegal_combination(gt, 'gt', le, 'le', location, raise_error, log)
            return False
        if lt is not None and gt >= lt:
            illegal_combination(gt, 'gt', lt, 'lt', location, raise_error, log)
            return False
    return True


def illegal_value(value, name, location=None, raise_error=False, log=True):
    """Print illegal value message and/or raise error.

    :param value: Input value.
    :param name: Value name.
    :type name: str
    :param location: Input location.
    :type location: str, optional
    :param raise_error: Raise an error, defaults to `False`.
    :type raise_error: bool, optional
    :param log: Write error message to the logger, defaults to `True`.
    :type log: bool, optional
    :raise: ValueError when `raise_error` is set to `True`.
    """
    if not isinstance(location, str):
        location = ''
    else:
        location = f'in {location} '
    if isinstance(name, str):
        error_msg = \
            f'Illegal value for {name} {location}({value}, {type(value)})'
    else:
        error_msg = f'Illegal value {location}({value}, {type(value)})'
    if log:
        logger.error(error_msg)
    if raise_error:
        raise ValueError(error_msg)


def illegal_combination(
        value1, name1, value2, name2, location=None, raise_error=False,
        log=True):
    """Print illegal combination message and/or raise error.

    :param value1: Input value.
    :param name1: Value name.
    :type name1: str
    :param value2: Input value.
    :param name2: Value name.
    :type name2: str
    :param location: Input location.
    :type location: str, optional
    :param raise_error: Raise an error, defaults to `False`.
    :type raise_error: bool, optional
    :param log: Write error message to the logger, defaults to `True`.
    :type log: bool, optional
    :raise: ValueError when `raise_error` is set to `True`.
    """
    if not isinstance(location, str):
        location = ''
    else:
        location = f'in {location} '
    if isinstance(name1, str):
        error_msg = f'Illegal combination for {name1} and {name2} {location}' \
            f'({value1}, {type(value1)} and {value2}, {type(value2)})'
    else:
        error_msg = f'Illegal combination {location}' \
            f'({value1}, {type(value1)} and {value2}, {type(value2)})'
    if log:
        logger.error(error_msg)
    if raise_error:
        raise ValueError(error_msg)
