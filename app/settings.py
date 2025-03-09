from enum import Enum


# mu/loc of the normal continuous random variable
LOC = 1.5

# matplotlib settings
MPL_RUNTIME_CONFIG = {
    "axes.spines.right": False,
    "axes.spines.top": False,
    "figure.dpi": 200,
    "font.family": "Arial"
}


class SigmaSupremum(Enum):
    """
    Unreachable upper bound of the sigma interval that corresponds
    to the quality class.

    E.g., RED class never reaches sigma=2.1 supremum which is the
    exact lower bound of the next, YELLOW, class and YELLOW never
    reaches 4.1 which is the lower bound of the GREEN class.
    """

    RED = 2.1
    YELLOW = 4.1
    # GREEN = float("inf")
