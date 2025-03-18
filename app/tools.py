import io
import json
import math
import operator
from dataclasses import dataclass
from types import NoneType

import matplotlib.pyplot as plt
import mplcyberpunk
import numpy
from fastapi import Response
from matplotlib.ticker import FormatStrFormatter
from scipy.stats import norm as norm_rv

from .settings import LOC, MPL_RUNTIME_CONFIG


# select Anti-Grain Geometry backend to prevent "UserWarning:
# Starting a Matplotlib GUI outside of the main thread will likely fail."
# https://matplotlib.org/stable/users/explain/figure/backends.html#backends
plt.rcParams.update(MPL_RUNTIME_CONFIG)
plt.style.use("cyberpunk")
plt.switch_backend("agg")

# normal continuous random variable with loc=LOC and scale=1 (default)
# https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html
norm = norm_rv(LOC)


class Plotter:
    """
    Helper class to plot sigma and defect rate of a process.
    """

    def __init__(self, process_list) -> None:
        self.process_list = process_list
        self._buffer      = io.BytesIO()
        self._dumps       = []
        self._plot_process()

    def _plot_process(self) -> None:
        """Plot sigma and defect rate of a process. """
        nrows = len(self.process_list)
        fig, ax = plt.subplots(
            nrows=nrows, figsize=(8, 2.2*nrows), squeeze=False
        )
        plt.subplots_adjust(hspace=0.5)
        ax_iter = ax.flat

        xmin, xmax = -3, 6
        x = numpy.linspace(xmin, xmax, 100*(xmax - xmin) + 1)
        y = norm.pdf(x)  # probability density function
        xticks = list(range(xmin, xmax + 1)) + [LOC]

        for process in self.process_list:
            dump = process.model_dump()
            self._dumps.append(dump)
            tests, fails, name, defect_rate, sigma, label = dump.values()
            sigma_clamped = max(xmin, min(sigma, xmax))
            xfill = numpy.linspace(sigma_clamped, xmax)

            dr_label = f"Defect rate = {defect_rate * 100:.2f}%"
            aes = {"label": dr_label, "color": label.lower(), "alpha": 0.44}
            norm_label = f"$N(\\mu = {LOC}, \\sigma = 1)$"
            sigma_annotation = f"$\\sigma$ = {sigma:.3f}"
            name = f", {name=}" if name else ""
            title = f"{process.__class__.__name__}({tests=}, {fails=}{name})"

            ax = next(ax_iter)
            ax.plot(x, y, lw=1.2, label=norm_label)
            ax.fill_between(xfill, norm.pdf(xfill), 0, **aes)
            ax.annotate(sigma_annotation, size=15, xy=(0.84, 0.2))
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(0, y.max() + 0.03)
            ax.set_xticks(xticks)
            ax.tick_params(axis="both", labelsize=8)
            ax.xaxis.set_major_formatter(FormatStrFormatter("%.2g"))
            ax.grid(lw=0.6)
            ax.legend(frameon=True, framealpha=1, loc="upper left")
            ax.set_title(title)

            mplcyberpunk.make_lines_glow(ax=ax)
            mplcyberpunk.add_underglow(ax=ax)

        plt.savefig(self._buffer, bbox_inches="tight", format="png")
        plt.close(fig)

    @property
    def response(self) -> Response:
        """Response with a plot. """
        return Response(
            content=self._buffer.getvalue(),
            headers={
                "Content-Disposition": "inline; filename=plot.png",
                "Process-List"       : json.dumps(self._dumps)
            },
            media_type="image/png"
        )


class Comparator:
    """
    Class implementing field type-sensitive equality test.
    """

    _compare_funcs = {
        NoneType: operator.eq,
        str     : operator.eq,
        int     : operator.eq,
        float   : math.isclose
    }

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return all(
                self.__class__._compare_funcs[type(v)](v, other.__dict__[k])
                for k, v in self.__dict__.items()
            )
        return NotImplemented


@dataclass(eq=False)
class ComparableSberProcess(Comparator):
    """
    SberProcess dump with field type-sensitive equality test.
    """

    tests      : int
    fails      : int
    defect_rate: float
    sigma      : float
    label      : str
    name       : str | None = None
