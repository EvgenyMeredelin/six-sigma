## Simple web app to evaluate a process with the SIX SIGMA approach

#### Request URL
```
https://six-sigma.containers.cloud.ru/chart?tests=1500&fails=123&name=Example%20process
```

#### Response headers
```
"content-type": "image/png",
"content-length": "323561",
"content-disposition": "inline; filename=chart.png",
"date": "Thu, 31 Oct 2024 21:51:56 GMT",
"process-defect_rate": "0.082",
"process-fails": "123",
"process-label": "YELLOW",
"process-name": "Example process",
"process-sigma": "2.891743779396325",
"process-tests": "1500",
...
```

#### Response body
![plot](assets/chart.png)
