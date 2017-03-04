>**Note:**
>This Readme has been automatically created by [zepppelin2md.py](https://github.com/bernhard-42/zeppelin2md).

>Alternatively, to open the Zeppelin Notebook with [Zeppelin Viewer](https://www.zeppelinhub.com/viewer) use the URL 
>    `https://raw.githubusercontent.com/bernhard-42/advanced-angular-for-pyspark/master/Advanced%20Angular%20for%20Pyspark.json`

# Advanced Angular for Pyspark.json

---

## Some helper functions


---


_Input:_

```python
%pyspark
def display(html):
    print("%angular")
    print(html)

def getNoteId():
    return z.z.getInterpreterContext().getNoteId()

def getParagraphId():
    return z.z.getInterpreterContext().getParagraphId()
```


---


_Input:_

```python
%pyspark
print("Note Id:     ", getNoteId())
print("Paragraph Id:", getParagraphId())
```


_Result:_

```
Note Id:      2C9U3F8H6
Paragraph Id: 20170304-210119_1421749066

```

---


_Input:_

```python
%pyspark
print("Note Id:     ", getNoteId())
print("Paragraph Id:", getParagraphId())
```


_Result:_

```
Note Id:      2C9U3F8H6
Paragraph Id: 20170304-210236_2061754981

```

---


_Input:_

```python
%pyspark
display("<b>Hello Zeppelin</b>")
```


---

## How to trigger simple Javascript functions: DOM buttons


---


_Input:_

```python
%pyspark

display("""<button id="abcde" ng-click="run = run + 1">Click {{run}}</button>""")

setVar("run", 0)
```


---

## How to trigger Javascript functions: A custom watcher

Clicking on some DOM button is sometimes OK, however it would be great to have a way to trigger Javascript functions from Python.

So let's use the capabilities of `z.z.angularBind`, `z.z.angularUnbind` and `z.z.angular` together with `$scope.$watch` (the Angular way to trigger javascript functions based on changed variables)


---


_Input:_

```python
%pyspark
from uuid import uuid4
import time

INIT_TMPL = """
<script>
    var sessionCommVar = "%s";
    var sessionCommDivId = "%s"
    var execution_id = "%s"                                                // Avoid double execution
    if(window.__zeppelin_already_executed__ == null) {                     //
        window.__zeppelin_already_executed__ = [];                         //
    }                                                                      //
    if(!window.__zeppelin_already_executed__.includes(execution_id)) {     // Avoid double execution

        // Get the angular scope of the session div element
        console.log("Get scope for div id " + sessionCommDivId);
        var $scope = angular.element(document.getElementById(sessionCommDivId)).scope();

        // Remove any remaining watcher from last session
        if(typeof(window.__zeppelin_notebook_unwatchers__) !== "undefined") {
            console.info("ZeppelinSession: Cancel watchers");
            var unwatchers = window.__zeppelin_notebook_unwatchers__
            for(i in unwatchers) {
                unwatchers[i]();
            }
        }
        
        // Array to note all active watchers (as with their respective unwatcher function)
        window.__zeppelin_notebook_unwatchers__ = [];
        
        // make scope easily accessible in Web Console
        window.__zeppelin_comm_scope = $scope;

        console.info("Install Angular watcher for session comm var " + sessionCommVar);
        var unwatch = $scope.$watch(sessionCommVar, function(newValue, oldValue, scope) {
            
            // The global message handler
            
            if(typeof(newValue) !== "undefined") {

                if (newValue.task === "call") {

                    // Format: newValue = {"id": int, task":"call", "msg":{"function":"func_name", "object":"json_string"}}
                    
                    var data = newValue.msg;
                    if (typeof($scope.__functions[data.function]) === "function") {
                        $scope.__functions[data.function]($scope, data.object);
                    } else {
                        alert("Unknown function: " + data.function + "()")
                    }
                    
                } else if (newValue.task === "register") {
                    
                    // Format: newValue = {"id": int, task":"register", "msg":{"function":"func_name", "funcBody":"function_as_string"}}
                    
                    var data = newValue.msg;
                    var func = eval(data.funcBody);
                    $scope.__functions[data.function] = func;
                    
                } else if (newValue.task === "unregister") {
                    
                    // Format: newValue = {"id": int, task":"unregister", "msg":{"function":"func_name"}}
                    
                    var data = newValue.msg;
                    if (typeof($scope.__functions[data.function]) === "function") {
                        delete $scope.__functions[data.function];
                    }               
                    
                } else if (newValue.task === "dump") {
                    
                    // Format: newValue = {"id": int, task":"dump", "msg":{}}
                    
                    console.log("sessionCommDivId: ", sessionCommDivId);
                    console.log("$scope: ", $scope);
                    
                } else {
                    alert("Unknown task: " + JSON.stringify(newValue));
                }
            }
        }, true)
        
        // Initialize the object that will hold the registered functions
        $scope.__functions = {};
        
        // remember unwatch function to clean up later
        window.__zeppelin_notebook_unwatchers__.push(unwatch)
        
        // mark init as executed
        window.__zeppelin_already_executed__.push(execution_id);            // Avoid double execution
    } else {                                                                //
        console.info("Angular script already executed, skipped");           //
    }                                                                       // Avoid double execution
</script>
"""


class ZeppelinSession:

    def __init__(self, zeppelinContext, delay=0.1):
        self.id = 0
        self.delay = delay
        self.zeppelinContext = zeppelinContext

    def sessionVars(self, all=True):
        noteId = self.zeppelinContext.getInterpreterContext().getNoteId()
        sessionCommVar = "__zeppelin_comm_%s_msg__" % noteId
        if all:
            sessionCommDivId = "__Zeppelin_Session_%s_Comm__" % noteId
            sessionStatusVar = "__zeppelin_comm_%s_status__" % noteId
            return (sessionCommDivId, sessionCommVar, sessionStatusVar)
        else:
            return sessionCommVar

    def init(self, jsScript=None):
        sessionCommDivId, sessionCommVar, sessionStatusVar = self.sessionVars(all=True)
        self.zeppelinContext.angularUnbind(sessionCommVar)
        self.zeppelinContext.angularUnbind(sessionStatusVar)

        # div must exist before javascript below can be printed
        print("%angular")
        if jsScript:
            print("""<script>{{%s}}</script>\n""" % jsScript)
        print("""<div id="%s">{{%s}}</div>\n""" % (sessionCommDivId, sessionStatusVar))
        self.zeppelinContext.angularBind(sessionStatusVar, "Session initialized, can now be started in the next paragraph ...  (do not delete this paragraph)")

    def start(self):
        sessionCommDivId, sessionCommVar, sessionStatusVar = self.sessionVars(all=True)

        self.zeppelinContext.angularBind(sessionStatusVar, "ZeppelinSession started (do not delete this paragraph)")
        print("%angular") 
        print(INIT_TMPL % (sessionCommVar, sessionCommDivId, str(uuid4())))
        
    def send(self, task, msg):
        sessionCommVar = self.sessionVars(all=False)
        self.id += 1 # ensure every message is different
        self.zeppelinContext.angularBind(sessionCommVar, {"id": self.id, "task":task, "msg":msg})
    
    def registerFunction(self, funcName, jsFunc):
        self.send("register", {"function": funcName, "funcBody": jsFunc})
    
    def unregisterFunction(self, funcName):
        self.send("unregister", {"function": funcName})

    def call(self, funcName, object):
        self.send("call", {"function": funcName, "object": object})
        
    def set(self, var, value):
        self.zeppelinContext.angularBind(var, value)
        
    def get(self, var, delay=0.2):
        time.sleep(delay)
        return self.zeppelinContext.angular(var)
        
    def delete(self, var):
        self.zeppelinContext.angularUnbind(var)
        
    def dumpScope(self):
        self.send("dump", {})
        
    
```


---

**Note:** All variables and functions created by the methods of this class are bound to the paragraph that executes the `init` method. So don't mix it up with `z.z.angularBind` / `z.z.angularUnbind`


---

#### Create a new session

_Input:_

```python
%pyspark

session = ZeppelinSession(z.z)
session.init()
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
session.set("myvar", 10)
session.get("myvar")
```


_Result:_

```
10

```

---

**Note:**
Angular calls are async. This can't be controlled from Python, so `session.get` my be called "too early", i.e. before Angular has finished its `$apply()` call.

That's why `session.get` has an additional parameter `delay` (default 200ms) to give Angular a chance to finish. 

Example: `session.get("myvar", 0.5)` for 500ms


---

#### Registering a javascript function

- session: All variables created via the ZeppelinSession class can be accessed via the `scope` parameter (which actually is $scope of the Zeppelin Session DIV element)
- object: The `object`parameter can be defined as needed and has to be in sync with the parameter given in `session.call`


---


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

#### Calling the registered function

_Input:_

```python
%pyspark
session.call("increment", {"inc":32})

# Remember: async call above, so result might be outdated!

session.get("myvar")
```


_Result:_

```
42

```

---


_Input:_

```python
%pyspark
session.get("myvar")
```


_Result:_

```
42

```

---

#### Finally unregister the function again

_Input:_

```python
%pyspark
session.unregisterFunction("increment")
```


---

#### Log $scope to Browsers Web Console for inspection

_Input:_

```python
%pyspark
session.dumpScope()
```


---


_Input:_

```python
%pyspark
```

