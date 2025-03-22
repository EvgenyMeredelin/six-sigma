import json
from collections.abc import Callable
from functools import wraps

from fastapi import status
# https://fastapi.tiangolo.com/tutorial/testing/#testing
from fastapi.testclient import TestClient

from .main import app, custom_openapi
from .settings import LOC
from .tools import ComparableDump


client = TestClient(app)


def assert_ok(test: Callable) -> Callable:
    """Assertion that actual processes respectively match the expected. """
    @wraps(test)
    def wrapper(*args, **kwargs) -> None:
        response, expected_dumps = test(*args, **kwargs)
        assert response.status_code == status.HTTP_200_OK
        actual_dumps = json.loads(response.headers["Process-List"])
        assert all(
            ComparableDump(**actual) == ComparableDump(**expected)
            for actual, expected in zip(actual_dumps, expected_dumps)
        )
    return wrapper


def assert_nok(test: Callable) -> Callable:
    """Assertion that app fails due to invalid input data. """
    @wraps(test)
    def wrapper(*args, **kwargs) -> None:
        response, expected_response_body = test(*args, **kwargs)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json() == expected_response_body
    return wrapper


@assert_nok
def test_zero_tests_zero_fails():
    """Single process. tests = 0, fails = 0. """
    response = client.get(
        url="/plot",
        params={"tests": 0, "fails": 0}
    )
    expected_response_body = {
        "detail": [
            {
                "type" : "greater_than",
                "loc"  : ["query", "tests"],
                "msg"  : "Input should be greater than 0",
                "input": "0",
                "ctx"  : {"gt": 0}
            },
            {
                "type" : "greater_than",
                "loc"  : ["query", "fails"],
                "msg"  : "Input should be greater than 0",
                "input": "0",
                "ctx"  : {"gt": 0}
            }
        ]
    }
    return response, expected_response_body


@assert_nok
def test_negative_tests_negative_fails():
    """Single process. tests < 0, fails < 0. """
    response = client.get(
        url="/plot",
        params={"tests": -50, "fails": -25}
    )
    expected_response_body = {
        "detail": [
            {
                "type" : "greater_than",
                "loc"  : ["query", "tests"],
                "msg"  : "Input should be greater than 0",
                "input": "-50",
                "ctx"  : {"gt": 0}
            },
            {
                "type" : "greater_than",
                "loc"  : ["query", "fails"],
                "msg"  : "Input should be greater than 0",
                "input": "-25",
                "ctx"  : {"gt": 0}
            }
        ]
    }
    return response, expected_response_body


@assert_nok
def test_fails_greater_than_tests():
    """Single process. fails > tests. """
    response = client.get(
        url="/plot",
        params={"tests": 50, "fails": 51}
    )
    expected_response_body = {
        "detail": "Number of fails can't be greater than the total number of tests"
    }
    return response, expected_response_body


@assert_nok
def test_string_tests_string_fails():
    """Single process. fails: str, tests: str. """
    response = client.get(
        url="/plot",
        params={"tests": "tests", "fails": "fails"}
    )
    expected_response_body = {
        "detail": [
            {
                "type" : "int_parsing",
                "loc"  : ["query", "tests"],
                "msg"  : "Input should be a valid integer, unable to parse string as an integer",
                "input": "tests"
            },
            {
                "type" : "int_parsing",
                "loc"  : ["query", "fails"],
                "msg"  : "Input should be a valid integer, unable to parse string as an integer",
                "input": "fails"
            }
        ]
    }
    return response, expected_response_body


@assert_ok
def test_float_coercible_to_integer():
    """Single process. tests and fails are floats coercible to integer. """
    response = client.get(
        url="/plot",
        params={"tests": 50.0, "fails": 25.0}
    )
    expected_dumps = [
        {
            "tests"      : 50,
            "fails"      : 25,
            "defect_rate": 0.5,
            "sigma"      : LOC,
            "label"      : "RED"
        }
    ]
    return response, expected_dumps


@assert_ok
def test_fails_thresholds_for_one_million_tests():
    """Multiple processes. Fails thresholds for 1M tests. """
    response = client.post(
        url="/plot",
        json=[
            {
                "tests": 1e6,
                "fails": 274254,
                "name" : "Red class..."
            },
            {
                "tests": 1e6,
                "fails": 274253,
                "name" : "...turned Yellow"
            },
            {
                "tests": 1e6,
                "fails": 4662,
                "name" : "...is still Yellow"
            },
            {
                "tests": 1e6,
                "fails": 4661,
                "name" : "...and now it's Green"
            }
        ]
    )
    expected_dumps = [
        {
            "tests"      : 1_000_000,
            "fails"      : 274254,
            "name"       : "Red class...",
            "defect_rate": 0.274254,
            "sigma"      : 2.0999973523886952,
            "label"      : "RED"
        },
        {
            "tests"      : 1_000_000,
            "fails"      : 274253,
            "name"       : "...turned Yellow",
            "defect_rate": 0.274253,
            "sigma"      : 2.1000003533655227,
            "label"      : "YELLOW"
        },
        {
            "tests"      : 1_000_000,
            "fails"      : 4662,
            "name"       : "...is still Yellow",
            "defect_rate": 0.004662,
            "sigma"      : 4.099940225647758,
            "label"      : "YELLOW"
        },
        {
            "tests"      : 1_000_000,
            "fails"      : 4661,
            "name"       : "...and now it's Green",
            "defect_rate": 0.004661,
            "sigma"      : 4.10001384285712,
            "label"      : "GREEN"
        }
    ]
    return response, expected_dumps


def test_redirect_to_docs():
    """Test redirect from root to FastAPI Swagger docs. """
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert str(response.url).endswith("/docs")


def test_custom_openapi():
    """Test `custom_openapi` works as expected. """
    # check if the app.openapi method is customized
    assert app.openapi == custom_openapi

    # check there's currently no OpenAPI schema
    assert app.openapi_schema is None

    # produce the schema and check it's there
    app.openapi()
    assert app.openapi_schema is not None

    app.openapi()
    # custom_openapi's first return statement
    # returns previously produced schema,
    # so the statement is now fully covered
