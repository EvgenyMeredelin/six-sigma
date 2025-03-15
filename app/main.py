from functools import cached_property
from typing import Self

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    status
)
from fastapi.openapi.utils import get_openapi
from pydantic import (
    BaseModel,
    computed_field,
    model_validator,
    PositiveInt
)
from starlette.responses import RedirectResponse

from .settings import MAX_ROWS, SigmaSupremum
from .tools import norm, Plotter


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
            "name" : "Evgeny Meredelin",
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
async def plot_single_process(process: SberProcess = Depends()):
    return Plotter([process]).response


@app.post("/plot")
async def plot_process_list(process_list: list[SberProcess]):
    return Plotter(process_list[:MAX_ROWS]).response
