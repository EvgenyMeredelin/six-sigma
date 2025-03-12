from functools import cached_property
from io import BytesIO
from typing import Self

import matplotlib.pyplot as plt
import mplcyberpunk
import numpy as np
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Response,
    status
)
from fastapi.openapi.utils import get_openapi
from matplotlib.ticker import FormatStrFormatter
from pydantic import (
    BaseModel,
    computed_field,
    model_validator,
    PositiveInt
)
from scipy.stats import norm as norm_rv
from starlette.responses import RedirectResponse

from .settings import *


plt.rcParams.update(MPL_RUNTIME_CONFIG)
plt.style.use("cyberpunk")

# normal continuous random variable with loc=LOC and scale=1 (default)
# https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html
norm = norm_rv(LOC)


class SberProcess(BaseModel):
    """
    Process to evaluate with the "6 Sigma" approach.
    """

    tests: PositiveInt          # total number of tests
    fails: PositiveInt          # number of tests qualified as failed
    name : str | None = None    # name of the process (optional)

    @model_validator(mode="after")
    def prevent_fails_gt_tests(self) -> Self:
        if self.fails > self.tests:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Number of fails can't be greater than the total"
                    " number of tests"
                )
            )
        return self

    @computed_field
    @cached_property
    def defect_rate(self) -> float:
        return self.fails / self.tests

    @computed_field
    @cached_property
    def sigma(self) -> float:
        # percent point function
        return norm.ppf(1 - self.defect_rate).item()

    @computed_field
    @cached_property
    def label(self) -> str:
        for supremum in SigmaSupremum:
            if self.sigma < supremum.value:
                return supremum.name
        return "GREEN"


def plot_process(process_list: list[SberProcess]) -> Response:
    """
    Plot sigma and defect rate of a process and return response with an image.
    """
    nrows = len(process_list)
    fig, ax = plt.subplots(
        nrows=nrows, figsize=(8, 2.2*nrows), squeeze=False
    )
    plt.subplots_adjust(hspace=0.5)
    ax_iter = ax.flat

    xmin, xmax = -3, 6
    x = np.linspace(xmin, xmax, 100*(xmax - xmin) + 1)
    y = norm.pdf(x)  # probability density function
    xticks = list(range(xmin, xmax + 1)) + [LOC]

    for process in process_list:
        tests, fails, name, defect_rate, sigma, label = (
            process.model_dump().values()
        )
        sigma_clamped = max(xmin, min(sigma, xmax))
        xfill = np.linspace(sigma_clamped, xmax)

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

    image_buffer = BytesIO()
    plt.savefig(image_buffer, bbox_inches="tight", format="png")
    plt.close(fig)

    return Response(
        content=image_buffer.getvalue(),
        headers={"Content-Disposition": "inline; filename=plot.png"},
        media_type="image/png"
    )


app = FastAPI()


def custom_openapi():
    """
    Generate the OpenAPI custom schema of the application.
    https://fastapi.tiangolo.com/how-to/extending-openapi/#extending-openapi
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Six Sigma",
        version="0.1.0",
        routes=app.routes,
        contact={
            "name": "Evgeny Meredelin",
            "email": "eimeredelin@sberbank.ru"
        }
    )

    app.openapi_schema = openapi_schema
    return openapi_schema


app.openapi = custom_openapi


@app.get("/")
async def redirect_from_root_to_docs():
    return RedirectResponse(url="/docs")


@app.get("/plot")
async def plot_single_process(process: SberProcess = Depends()) -> Response:
    return plot_process([process])


@app.post("/plot")
async def plot_process_list(process_list: list[SberProcess]) -> Response:
    return plot_process(process_list[:MAX_ROWS])
