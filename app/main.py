# standard library
import math
from functools import cached_property
from typing import Annotated, Literal, Self

# third-party libraries
import logfire
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Path,
    status
)
from pydantic import (
    BaseModel,
    Field,
    computed_field,
    model_validator,
    NonNegativeInt,
    PositiveInt
)
from starlette.responses import RedirectResponse

# user modules
from .settings import MAX_ROWS, SigmaSupremum
from .tools import norm_rv, plot_sigma


# valid `mode` path parameters and their respective handlers
mode_handlers = {
    # data-only option, process(-es) enriched with computed fields
    "data": lambda process_list: process_list,
    # image as binary output and data in the "Process-List" header
    "plot": plot_sigma
}
Mode = Literal[tuple(mode_handlers)]


class SberProcess(BaseModel):
    """
    Process to evaluate with the "6 Sigma" approach.
    """

    tests: Annotated[
        PositiveInt,
        Field(description="Total number of tests")
    ]
    fails: Annotated[
        NonNegativeInt,
        Field(description="Number of tests qualified as failed")
    ]
    name: Annotated[
        str | None,
        Field(description="Name of the process (optional)")
    ] = None

    @model_validator(mode="after")
    def prevent_fails_greater_than_tests(self) -> Self:
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
    def sigma(self) -> float | str:
        # percent point function
        value = norm_rv.ppf(1 - self.defect_rate).item()
        # out of range float values are not JSON compliant
        if math.isinf(value):
            return "-inf" if value < 0 else "inf"
        return value

    @computed_field
    @cached_property
    def label(self) -> str:
        # if sigma in {"-inf", "inf"}
        sigma = float(self.sigma)
        for sup in SigmaSupremum:
            if sigma < sup.value:
                return sup.name
        return sup.name


app = FastAPI(
    title="Six Sigma",
    description=(
        "Simple web app to evaluate a process "
        "with the \"6 Sigma\" approach"
    ),
    version="0.1.0",
    contact={
        "name" : "Evgeny Meredelin",
        "email": "eimeredelin@sberbank.ru"
    }
)
logfire.instrument_fastapi(
    app=app,
    capture_headers=True,
    record_send_receive=True
)


def handle_request(
    mode: Mode,  # type: ignore
    # either single process in the list or a bulk
    process_list: list[SberProcess]
):
    return mode_handlers[mode](process_list)


@app.get("/")
async def redirect_from_root_to_docs():
    return RedirectResponse(url="/docs")


@app.get("/{mode}")
def single(
    mode: Annotated[Mode, Path()],  # type: ignore
    process: Annotated[SberProcess, Depends()]
):
    return handle_request(mode, [process])


@app.post("/{mode}")
def bulk(
    mode: Annotated[Mode, Path()],  # type: ignore
    process_bulk: list[SberProcess]
):
    return handle_request(mode, process_bulk[:MAX_ROWS])
