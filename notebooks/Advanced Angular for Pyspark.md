>**Note:**
>This Readme has been automatically created by [zepppelin2md.py](https://github.com/bernhard-42/zeppelin2md).

>Alternatively, load into your Zeppelin instance using the URL 
>    `https://raw.githubusercontent.com/bernhard-42/advanced-angular-for-pyspark/master/notebooks/Advanced%20Angular%20for%20Pyspark.json`

# notebooks/Advanced Angular for Pyspark.json

---

#### Some helper functions

_Input:_

```python
%pyspark

def versionCheck():
    import sys
    print("Python: " + sys.version.replace("\n", " - "))
    print("Spark:  " + sc.version)

def display(html):
    print("%angular")
    print(html)

def getNoteId():
    return z.z.getInterpreterContext().getNoteId()

def getParagraphId():
    return z.z.getInterpreterContext().getParagraphId()


versionCheck()
```


_Result:_

```
Python: 3.5.2 |Anaconda 4.3.0 (x86_64)| (default, Jul  2 2016, 17:52:12)  - [GCC 4.2.1 Compatible Apple LLVM 4.2 (clang-425.0.28)]
Spark:  2.1.0

```

---

#### Simple Angular variable binding

_Input:_

```python
%pyspark

display("""

<b>Hello {{name}} !</b>
<div>Note Id:      <i>"%s"</i> (see browser address line)</div>
<div>Paragraph Id: <i>"%s"</i> (see paragraph menu)</div>

""" % (getNoteId(), getParagraphId()))

z.z.angularBind("name", "Zeppelin")
```


---


_Input:_

```python
%pyspark

z.z.angularBind("name", "Apache Zeppelin")
```


---

#### Trigger simple Javascript functions via DOM buttons

_Input:_

```python
%pyspark

display("""<button id="abcde" ng-click="run = run + 1">Click {{run}}</button>""")

z.z.angularBind("run", 0)
```


---

## How to trigger Javascript functions: ZeppelinSession, a custom Angular watcher

Clicking on some DOM button is sometimes OK, however it would be great to have a way to trigger Javascript functions from Python.

So let's use the capabilities of `z.z.angularBind`, `z.z.angularUnbind` and `z.z.angular` together with `$scope.$watch` (the Angular way to trigger javascript functions based on changed variables). This is implemnted in the class ZeppelinSession.

Preparation step on the machine running Zeppelin Server:

```
git clone https://github.com/bernhard-42/advanced-angular-for-pyspark
cd advanced-angular-for-pyspark
pip install zeppelin_session    # use the pip command of the python installation used in Zeppelin
```


---

#### Create a new session

_Input:_

```python
%pyspark

from zeppelin_session import ZeppelinSession, resetZeppelinSession

resetZeppelinSession(z.z)
session = ZeppelinSession(z.z)
```


---

#### Start the session (means start Angular watching)

_Input:_

```python
%pyspark
session.start()
```


---

#### Set and get Javascript variables from python

_Input:_

```python
%pyspark
session.setVar("myvar", 10)
session.getVar("myvar")
```


_Result:_

```
10

```

---

**Note:**
Angular calls are async. This can't be controlled from Python, so `session.getVar` my be called "too early", i.e. before Angular has finished its `$apply()` call.

That's why `session.getVar` has an additional parameter `delay` (default 200ms) to give Angular a chance to finish. 

Example: `session.getVar("myvar", 500)` for 500ms


---

#### Registering a javascript function

_Input:_

```python
%pyspark

jsFunc = """
increment = function(session, object) {
    session.myvar +=  object.inc
}
"""
session.registerFunction("increment", jsFunc)
```


---

**Note:**
The first parameter, `session`, is actually the Angular scope. So every variable `xyz` bound via `z.z.angularBind` can be accessed and changed in the function vie `session.xyz`


---

#### Calling the registered function

_Input:_

```python
%pyspark
session.call("increment", object={"inc":32})

session.getVar("myvar", delay=1000) # Remember: async call above, so result might be outdated!
```


_Result:_

```
74

```

---

#### Finally unregister the function again

_Input:_

```python
%pyspark

session.unregisterFunction("increment")

session.call("increment", object={"inc":32}) # will now show "Unknown function: increment()" in the Browser Javascript Console
```


---

#### Log $scope to Browsers Web Console for inspection

_Input:_

```python
%pyspark
session._dumpScope()
```


_Result:_

```
Open the Browser Javascript Console to examine the Angular $scope that holds the Zeppelin Session

```

---


_Input:_

```python
%pyspark
```

