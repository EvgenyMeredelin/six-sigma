# standard library
from enum import Enum
from io import BytesIO
from typing import Self

# 3rd party modules
import matplotlib.pyplot as plt
import numpy as np
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Response,
    status
)
from matplotlib.ticker import FormatStrFormatter
from pydantic import (
    BaseModel,
    computed_field,
    model_validator,
    PositiveInt
)
from scipy.stats import norm as norm_rv
from starlette.responses import RedirectResponse


# mu/loc of the normal continuous random variable
LOC = 1.5

# normal continuous random variable with loc=1.5 and scale=1 (default)
# https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html
norm = norm_rv(LOC)

runtime_config = {
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.titlepad": 15,
    "figure.dpi": 600,
    "font.family": "sans serif"
}
plt.rcParams.update(runtime_config)
plt.style.use("seaborn-v0_8-colorblind")


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


class SberProcess(BaseModel):
    """
    Process to evaluate with the SIX SIGMA approach.
    """

    tests: PositiveInt       # total number of tests
    fails: PositiveInt       # number of tests qualified as failed
    name: str | None = None  # name of the process (optional)

    @model_validator(mode="after")
    def prevent_fails_gt_tests(self) -> Self:
        if self.fails > self.tests:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="`fails` can't be greater than `tests`"
            )
        return self

    @computed_field
    @property
    def defect_rate(self) -> float:
        return self.fails / self.tests

    @computed_field
    @property
    def sigma(self) -> float:
        # percent point function
        return norm.ppf(1 - self.defect_rate).item()

    @computed_field
    @property
    def label(self) -> str:
        for supremum in SigmaSupremum:
            if self.sigma < supremum.value:
                return supremum.name
        return "GREEN"

    def plot_sigma_chart(self) -> BytesIO:
        tests, fails, name, defect_rate, sigma, label = (
            getattr(self, attr_name) for attr_name in self.model_dump()
        )
        xmin, xmax = -3, 6
        x = np.linspace(xmin, xmax, 100*(xmax - xmin) + 1)
        y = norm.pdf(x)  # probability density function
        xticks = list(range(xmin, xmax + 1)) + [LOC]
        sigma_clamped = max(xmin, min(sigma, xmax))
        xfill = np.linspace(sigma_clamped, xmax)

        dr_label = f"Defect rate = {defect_rate * 100:.2f}%"
        aes = {"label": dr_label, "color": label.lower(), "alpha": 0.6}
        norm_label = f"$N(\\mu = {LOC}, \\sigma = 1)$"
        sigma_annotation = f"$\\sigma$ = {str(sigma)[:5 + (sigma < 0)]}"
        name = f", {name=!r}" if name else ""
        title = f"{self.__class__.__name__}({tests=}, {fails=}{name})"

        fig = plt.figure(figsize=(8, 1.8))
        plt.plot(x, y, lw=1.2, color="k", label=norm_label)
        plt.fill_between(xfill, norm.pdf(xfill), 0, **aes)
        plt.annotate(sigma_annotation, size=15, xy=(0.75, 0.2))
        plt.xlim(xmin, xmax)
        plt.ylim(0, y.max() + 0.02)
        plt.xticks(xticks)
        plt.tick_params(axis="both", labelsize=8)
        plt.gca().xaxis.set_major_formatter(FormatStrFormatter("%.2g"))
        plt.grid(lw=0.5, axis="x", color="gainsboro")
        plt.legend(frameon=True, framealpha=1, loc="upper left")
        plt.title(title)

        image_buffer = BytesIO()
        plt.savefig(image_buffer, bbox_inches="tight", format="png")
        plt.close(fig)
        return image_buffer


app = FastAPI()


@app.get("/")
async def redirect():
    return RedirectResponse(url="/docs")


@app.get("/chart")
async def sigma_chart_and_data_in_headers(
    background_tasks: BackgroundTasks,
    process: SberProcess = Depends(),
):
    image_buffer = process.plot_sigma_chart()
    background_tasks.add_task(image_buffer.close)
    headers = {"Content-Disposition": "inline; filename=chart.png"}

    for attr_name, value in process.model_dump().items():
        header = "process-" + attr_name.replace("_", "-")
        headers[header] = str(value)

    return Response(
        content=image_buffer.getvalue(),
        headers=headers,
        media_type="image/png"
    )
