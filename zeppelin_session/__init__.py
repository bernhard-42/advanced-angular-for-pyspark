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

#  Session Messages:
#
#  Basic
#  - register    register a javascript function
#  - unregister  unregister a javascript function
#  - call        call a registered javascript function 
#  - dump        log $scope to Web Coinsole for debugging
# 

from uuid import uuid4
import time
from .logger import Logger, LogLevel


__ZEPPELIN_SESSION = {}
__ZEPPELIN_CONTEXT = None

def _JAVASCRIPT(sessionCommVar, sessionCommDivId):
    execution_id = str(uuid4())
    jsScript = """
<script>
    var sessionCommVar = "%s";
    var sessionCommDivId = "%s"
    var execution_id = "%s";                                                 // Avoid double execution
    if(window.__zeppelin_already_executed__ == null) {                       //
        window.__zeppelin_already_executed__ = [];                           //
    }                                                                        //
    if(!window.__zeppelin_already_executed__.includes(execution_id)) {       // Avoid double execution

        window.__zeppelin_session_debug = 0; // no debug output
        var Logger = function(name) {
            this.name = name;
        }
        Logger.prototype.info = function(msg) {
            if (window.__zeppelin_session_debug > 0) {
                console.info(this.name + " [INFO] " + msg)
            }
        }
        Logger.prototype.debug = function(msg) {
            if (window.__zeppelin_session_debug > 1) {
                console.log(this.name + " [DEBUG] " + msg)
            }
        }
        var logger = new Logger("ZeppelinSession");

        // Get the angular scope of the session div element

        logger.debug("Get scope for div id" + sessionCommDivId);
        var $scope = angular.element(document.getElementById(sessionCommDivId)).scope();

        // make scope easily accessible in Web Console

        window.__zeppelin_comm_scope = $scope;

        // Remove any remaining watcher from last session

        if(typeof(window.__zeppelin_notebook_unwatchers__) !== "undefined") {
            logger.info("ZeppelinSession: Cancel watchers");
            var unwatchers = window.__zeppelin_notebook_unwatchers__
            for(i in unwatchers) {
                unwatchers[i]();
            }
        }
        
        // Array to note all active watchers (as with their respective unwatcher function)

        window.__zeppelin_notebook_unwatchers__ = [];

        // Main Handler

        logger.info("Install Angular watcher for session comm var " + sessionCommVar);
        var unwatch = $scope.$watch(sessionCommVar, function(newValue, oldValue, scope) {
            if(typeof(newValue) !== "undefined") {
                // logger.info(newValue);
                if (newValue.task === "call") {

                    // Format: newValue = {"id": int, task":"call", "msg":{"function":"func_name", "object":"json_object", "delay":ms}}
                    
                    var data = newValue.msg;
                    logger.debug("Calling function " + data.function + " with delay: " + data.delay)

                    if (typeof($scope.__functions[data.function]) === "function") {
                        setTimeout(function() {
                            $scope.__functions[data.function]($scope, data.object);
                        }, data.delay);
                    } else {
                        console.error("Unknown function: " + data.function + "()")
                    }
                    
                } else if (newValue.task === "register") {
                    // Format: newValue = {"id": int, task":"register", "msg":{"function":"func_name", "funcBody":"function_as_string"}}
                    
                    var data = newValue.msg;
                    logger.debug("Registering function " + data.function)

                    var func = eval(data.funcName + "=" + data.funcBody);
                    $scope.__functions[data.function] = func;
                    
                } else if (newValue.task === "unregister") {
                    
                    // Format: newValue = {"id": int, task":"unregister", "msg":{"function":"func_name"}}
                    
                    var data = newValue.msg;
                    logger.debug("Unregistering function " + data.function)

                    if (typeof($scope.__functions[data.function]) === "function") {
                        delete $scope.__functions[data.function];
                    }               
                    
                } else if (newValue.task === "dump") {
                    
                    // Format: newValue = {"id": int, task":"dump", "msg":{}}
                    
                    logger.debug("sessionCommDivId: ", sessionCommDivId);
                    logger.debug("$scope: ", $scope);

                } else {

                    // Jupyter.notebook.kernel.session.handleMsg(newValue);

                    console.error("Unknown task: " + newValue.task)
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
        logger.info("Angular script already executed, skipped");           //
    }                                                                       // Avoid double execution
</script>
""" % (sessionCommVar, sessionCommDivId, execution_id)
    return jsScript


#
# Zeppelin Session Factory delivers one new object per Zeppelin Notebook
#

def ZeppelinSession(zeppelinContext=None):

    class ZeppelinSession:

        def __init__(self, zeppelinContext, ZS=None):
            self.zeppelinContext = zeppelinContext
            self.__ZS = ZS

            self.noteId = zeppelinContext.getInterpreterContext().getNoteId()

            self.logger = Logger(self.__class__.__name__).get()
            self.logger.propagate = False

            self.sessionId = str(uuid4())
            self.commId = 0

            self.logger.info("New ZeppelinSession %s" % self.sessionId)

            self.started = False


        #
        # Initialization methods.
        # 
        # init:  creates div
        # start: starts the communication system relying on the existence of the div (hence seaprate Zeppelin paragraph)
        #

        def init(self, _tag="%angular"):
            self.logger.info("Initializing ZeppelinSession %s" % self.sessionId)
            sessionCommDivId, sessionCommVar, sessionStatusVar = self._sessionVars(all=True)
            self.logger.debug("Reset $scope.%s" % sessionCommVar)
            self.zeppelinContext.angularUnbind(sessionCommVar)
            self.zeppelinContext.angularUnbind(sessionStatusVar)

            # div must exist before javascript below can be printed
            print(_tag)
            self.logger.debug("Print Zeppelin Session Comm div")
            print("""<div id="%s">{{%s}}</div>\n""" % (sessionCommDivId, sessionStatusVar))
            self.zeppelinContext.angularBind(sessionStatusVar, "Session initialized, can now be started in the next paragraph ...  " + 
                                                               "(do not delete this paragraph)")

        def start(self, _tag="%angular"):
            self.logger.debug("Starting %s ZeppelinSession" % self.sessionId)
            sessionCommDivId, sessionCommVar, sessionStatusVar = self._sessionVars(all=True)

            self.zeppelinContext.angularBind(sessionStatusVar, "ZeppelinSession started (do not delete this paragraph)")
            print(_tag)
            print("""<div>You should now see<br>""" + 
                  """<span style="margin:20px"><i>ZeppelinSession started (do not delete this paragraph)</i></span></br>""" +
                  """in the paragraph above</div>""")

            if not self.started:
                self.logger.debug("Loading Javascript Handler for session %s" % self.sessionId)            
                print(_JAVASCRIPT(sessionCommVar, sessionCommDivId))
                self.started = True
            else:
                self.logger.info("Javascript Handler for session %s already loaded" % self.sessionId)
        
        #
        # Helper methods
        #

        def _sessionVars(self, all=True):
            noteId = self.zeppelinContext.getInterpreterContext().getNoteId()
            sessionCommVar = "__zeppelin_comm_%s_msg__" % noteId
            if all:
                sessionCommDivId = "__Zeppelin_Session_%s_Comm__" % noteId
                sessionStatusVar = "__zeppelin_comm_%s_status__" % noteId
                return (sessionCommDivId, sessionCommVar, sessionStatusVar)
            else:
                return sessionCommVar

        def _dumpScope(self):
            self.send("dump", {})
            print("Open the Browser Javascript Console to examine the Angular $scope that holds the Zeppelin Session")

        def _reset(self):
            self.logger.debug("Resetting ZeppelinSession")
            sessionCommDivId, sessionCommVar, sessionStatusVar = self._sessionVars(all=True)
            time.sleep(0.2)
            self.zeppelinContext.angularUnbind(sessionCommVar)
            self.zeppelinContext.angularUnbind(sessionStatusVar)
            self.__ZS[self.noteId] = None

        #
        # Basic communication methods
        #

        def send(self, task, msg):
            sessionCommVar = self._sessionVars(all=False)
            self.logger.debug("Sending task %s to $scope.%s for message %s" % (task, sessionCommVar, msg))
            self.commId += 1
            self.zeppelinContext.angularBind(sessionCommVar, {"id": self.commId, "task":task, "msg":msg})

        #
        # Angular Variable handling
        #

        def setVar(self, var, value):
            self.logger.debug("Set var %s" % var)
            self.zeppelinContext.angularBind(var, value)
            
        def getVar(self, var, delay=200):
            self.logger.debug("Get var %s" % var)
            time.sleep(delay / 1000.0)
            return self.zeppelinContext.angular(var)
            
        def deleteVar(self, var):
            self.logger.debug("Delete var %s" % var)        
            self.zeppelinContext.angularUnbind(var)
            
        #
        # Angular Functions handling
        #

        def registerFunction(self, funcName, jsFunc):
            self.logger.info("Register function %s with: %s" % (funcName, jsFunc))        
            self.send("register", {"function": funcName, "funcBody": jsFunc})
        
        def unregisterFunction(self, funcName):
            self.logger.info("Unregister function %s" % funcName)
            self.send("unregister", {"function": funcName})

        def call(self, funcName, object, delay=200):
            self.logger.debug("Call function %s with delay %d" % (funcName, delay))
            self.send("call", {"function": funcName, "object": object, "delay":delay})
            

    #
    # Factory, only return one ZeppelinSession for each Zeppelin notebook
    #

    global __ZEPPELIN_SESSION
    global __ZEPPELIN_CONTEXT

    logger = Logger("ZeppelinSessionFactory").get()

    if zeppelinContext is None:
        logger.debug("Using cached ZeppelinContext")
        noteId = __ZEPPELIN_CONTEXT.getInterpreterContext().getNoteId()
    else:
        logger.debug("Using provided ZeppelinContext")
        noteId = zeppelinContext.getInterpreterContext().getNoteId()
        # save ZeppelinContext to allow later retrieval of session without parameter
        __ZEPPELIN_CONTEXT = zeppelinContext

    logger.info("Requesting session for Notebook %s (%s)" % (noteId, "None" if not __ZEPPELIN_SESSION.get(noteId)
                                                                            else __ZEPPELIN_SESSION.get(noteId).sessionId))
    if __ZEPPELIN_SESSION.get(noteId) is None:
        logger.debug("A new ZeppelinSession will be created for noteId %s" % noteId)
        __ZEPPELIN_SESSION[noteId] = ZeppelinSession(__ZEPPELIN_CONTEXT, ZS=__ZEPPELIN_SESSION)
         
         # Force ZeppelinSession.init()
        __ZEPPELIN_SESSION[noteId].init()
    else:
        logger.debug("Return existing ZeppelinSession")   
    
    logger.info("Notebook: %s ZeppelinSession: %s" % (noteId, __ZEPPELIN_SESSION.get(noteId).sessionId))
    
    return __ZEPPELIN_SESSION[noteId]


def resetZeppelinSession(zeppelinContext):
    global __ZEPPELIN_CONTEXT

    try:
        noteId = __ZEPPELIN_CONTEXT.getInterpreterContext().getNoteId()
        print("Resetting ZeppelinSession")
        if __ZEPPELIN_SESSION.get(noteId) is not None:
            __ZEPPELIN_SESSION.get(noteId)._reset()
    except AttributeError:
        pass

