# Logging HOWTO
## Basic Logging Tutorial
...
### When to use logging  

Convenience functions for simple logging usage:
- debug() 
- info()
- warning()
- error()
- critical()  

**Tasks and the best tool**  

|Task you want to perform| The best tool for the task |
|:---:                      |:---:
|Display console output for ordinary usage of a command line script or program         | print()|
|Report events that occur during normal operation of a program (e.g. for status monitoring or fault investigation)|logging.info() (or logging.debug() for very detailed output for diagnostic purposes)|
|Issue a warning regarding a particular runtime event | warnings.warn() in library code if the issue is avoidable and the client application should be modified to eliminate the warning logging.warning() if there is nothing the client application can do about the situation, but the event should still be noted |
|Report an error regarding a particular runtime event | Raise an exception|
|Report suppression of an error without raising an exception (e.g. error handler in a long-running server process)| logging.error(), logging.exception() or logging.critical() as appropriate for the specific error and application domain

**Function level and their applicability**  
In creasing order of the severity

|Level | When it's used
|:---: |:---:
|DEBUG |  Detailed information, typically of interest only when diagnosing problems
|INFO |  Confirmation that things are working as expected.
|WARNING | An indication that something unexpected happened, or indicative of some problem in the near future (e.g. 'disk space low'). The software is still working as expected
|ERROR | Due to a more serious problem, the software has not been able to perform some function
|CRITICAL | A serious error, indicating that the program itself may be unable to continue running

The default level is WARNING, which means that only events of this level and above will be tracked,
unless the logging package is configured to do otherwise.

Events that are tracked can be handled in different ways. Two common ways of handling:
- print them to the console
- write them to a disk file.
---
### A Simple Example
Run the script follows:
```python
import logging
logging.warning('Watch out!')  # will print a message to the console
logging.info('I told you so')  # will not print anything
```
... and the output is:
```
WARNING:root:Watch out!
```
---
### Logging to a file

The code follows will add logging information into a file:
```python
import logging
logging.basicConfig(filename='example.log',level=logging.DEBUG)
logging.debug('This message should go to the log file')
logging.info('So should this')
logging.warning('And this, too')
```
The call to basicConfig() should come before any calls to debug(), info() etc. As it's intended as a one-off 
simple configuration facility, only the first call will actually do anything: subsequent calls are effectively no-ops.

If you don't want to append the logs, use the code follows (add 'filemode' parameter'):
```python
logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)
```
---
### Logging from multiple modules
