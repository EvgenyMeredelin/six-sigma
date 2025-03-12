## Simple web app to evaluate a process with the "6 Sigma" approach

```python
import json
from io import BytesIO

import requests
from PIL import Image
```

```python
url = "https://six-sigma.containerapps.ru/plot"
```

```python
# https://six-sigma.containerapps.ru/plot?tests=1500&fails=256&name=Example%20process
params = {
    "tests": 1500,
    "fails": 256,
    "name": "Example process"
}
r = requests.get(url, params=params)
Image.open(BytesIO(r.content))
```

![plot](assets/single_process.png)

```python
data = [
    {
        "tests": 1e6,
        "fails": 274254,
        "name": "Red..."
    },
    {
        "tests": 1e6,
        "fails": 274253,
        "name": "...turned Yellow"
    },
    {
        "tests": 1e6,
        "fails": 4662,
        "name": "...is still Yellow"
    },
    {
        "tests": 1e6,
        "fails": 4661,
        "name": "...and now it's Green"
    }
]
r = requests.post(url, data=json.dumps(data))
Image.open(BytesIO(r.content))
```

![plot](assets/process_list.png)
