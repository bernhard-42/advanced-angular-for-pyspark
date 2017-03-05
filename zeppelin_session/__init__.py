# Copyright 2017 Bernhard Walter
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
        
  