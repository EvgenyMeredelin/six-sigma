from enum import Enum
from typing import Any


# mu/loc of the normal continuous random variable
LOC: int | float = 1.5

# maximum number of processes to plot on a figure
MAX_ROWS: int = 5

# matplotlib settings
MPL_RUNTIME_CONFIG: dict[str, Any] = {
    "axes.spines.right": False,
    "axes.spines.top"  : False,
    # "figure.dpi"       : 300,
    "font.family"      : "Arial"
}

# figure dpi
DPI_SINGLE: int = 300
DPI_LIST  : int = 120


class SigmaSupremum(Enum):
    """
    Unreachable upper bound of the sigma interval that corresponds
    to the quality class.

    E.g., RED class never reaches sigma=2.1 supremum which is the
    exact lower bound of the next, YELLOW, class and YELLOW never
    reaches 4.1 which is the lower bound of the GREEN class.
    """

    RED   : float = 2.1
    YELLOW: float = 4.1
    # GREEN : float = float("inf")
