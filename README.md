## Simple web app to evaluate a process with the "6 Sigma" approach

***
### Usage

```python
import json
from io import BytesIO

import requests
from PIL import Image
```

```python
# image as binary output and data in the "Process-List" header
url = "https://six-sigma.containerapps.ru/plot"

# data-only option, process(-es) enriched with computed fields
# see also https://github.com/EvgenyMeredelin/six-sigma-typer
url = "https://six-sigma.containerapps.ru/data"
```

```python
# https://six-sigma.containerapps.ru/plot?tests=1500&fails=256&name=Example%20process
params = {
    "tests": 1500,
    "fails": 256,
    "name" : "Example process"
}
r = requests.get(url, params=params)
Image.open(BytesIO(r.content))
```

![plot](assets/single.png)

```python
json.loads(r.headers["Process-List"])
```

```
[
    {
        "tests": 1500,
        "fails": 256,
        "name": "Example process",
        "defect_rate": 0.17066666666666666,
        "sigma": 2.4515340671620525,
        "label": "YELLOW"
    }
]
```

```python
data = [
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
r = requests.post(url, data=json.dumps(data))
Image.open(BytesIO(r.content))
```

![plot](assets/bulk.png)

```python
json.loads(r.headers["Process-List"])
```

```
[
    {
        "tests": 1000000,
        "fails": 274254,
        "name": "Red class...",
        "defect_rate": 0.274254,
        "sigma": 2.0999973523886952,
        "label": "RED"
    },
    {
        "tests": 1000000,
        "fails": 274253,
        "name": "...turned Yellow",
        "defect_rate": 0.274253,
        "sigma": 2.1000003533655227,
        "label": "YELLOW"
    },
    {
        "tests": 1000000,
        "fails": 4662,
        "name": "...is still Yellow",
        "defect_rate": 0.004662,
        "sigma": 4.099940225647758,
        "label": "YELLOW"
    },
    {
        "tests": 1000000,
        "fails": 4661,
        "name": "...and now it's Green",
        "defect_rate": 0.004661,
        "sigma": 4.10001384285712,
        "label": "GREEN"
    }
]
```

***
### Unit Tests & Coverage
```
$ pytest --cov-report term-missing --cov-report html:htmlcov --cov=. -vv
=============================== test session starts ================================
platform win32 -- Python 3.13.2, pytest-8.3.5, pluggy-1.5.0 -- D:\git\six-sigma\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\git\six-sigma
configfile: pytest.ini
plugins: anyio-4.9.0, logfire-3.19.0, cov-6.0.0
collected 9 items

test_main.py::test_no_tests_performed PASSED                                  [ 11%]
test_main.py::test_negative_tests_negative_fails PASSED                       [ 22%]
test_main.py::test_fails_greater_than_tests PASSED                            [ 33%]
test_main.py::test_string_tests_string_fails PASSED                           [ 44%]
test_main.py::test_float_coercible_to_integer PASSED                          [ 55%]
test_main.py::test_fails_equals_tests PASSED                                  [ 66%]
test_main.py::test_no_tests_failed PASSED                                     [ 77%]
test_main.py::test_fails_thresholds_for_one_million_tests PASSED              [ 88%]
test_main.py::test_redirect_to_docs PASSED                                    [100%]

---------- coverage: platform win32, python 3.13.2-final-0 -----------
Name           Stmts   Miss  Cover   Missing
--------------------------------------------
__init__.py        0      0   100%
main.py           51      0   100%
settings.py       11      0   100%
test_main.py      67      0   100%
tools.py          72      1    99%   116
--------------------------------------------
TOTAL            201      1    99%
Coverage HTML written to dir htmlcov


================================ 9 passed in 5.60s =================================
```
