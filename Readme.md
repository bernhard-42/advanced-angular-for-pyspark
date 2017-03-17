# Advanced Angular for Pyspark in Apache Zeppelin

## Overview

ZeppelinSession extends the Angular Backend API for Python with the capability to start javascript functions and pass objects to them from Python.

A quick overview can be found in the Zeppelin notebook: [Advanced Angular for Pyspark.json](notebooks/Advanced%20Angular%20for%20Pyspark.json). A readable version of notebook can be found under [Advanced Angular for Pyspark.md](notebooks/Advanced Angular%20for%20Pyspark.md).

**Note:**
The Session Layer consists of a Python and a Javascript. 

To turn on logging in Python, call 

```python
from zeppelin_session import ZeppelinSession, LogLevel

LogLevel().setLogLevel("DEBUG")

zs = ZeppelinSession(z.z)
```

To turn on logging for Javascript, go to the Browser web console and set

```javascript
__zeppelin_session_debug=0 // no logging
__zeppelin_session_debug=1 // info logging
__zeppelin_session_debug=2 // debug logging
```



## License

Copyright 2017 Bernhard Walter

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.