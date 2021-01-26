
# Object Relational Turorial (Official site tutorial)
## Version Check

## Connecting

## Declare a Mapping
process of configuration:
- describe the database tables we’ll be dealing with
- define our own classes which will be mapped to those tables
- these two tasks are performed together by SQLAlchemy, using 'Declarative'

> **declarative base class**:  
>- A base class which maintains a catalog of classes and tables relative to that base  
>- Usually just **ONE INSTANCE** in one application
>- Defined as follows:
>```python
> from sqlalchemy.ext.declarative import declarative_base
> Base = declarative_base()
>```
From now on, we uses an example '**user**', the definition is as follows:
- table: user
- class: User  

and the Python code of class User looks like:
```python
from sqlalchemy import Column, Integer, String
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    nickname = Column(String)
    
        
    # __repr__ is an built-in function of python class, this function prints formatted
    # info of one obj
    def __repr__(self):
       return "<User(name='%s', fullname='%s', nickname='%s')>" % (
                            self.name, self.fullname, self.nickname)
```

A class using Declarative at a minimum needs a \_\_tablename__ attribute, 
and at least one Column which is part of a primary key.

Outside of what the mapping process does to our class, the mapped class remains a
_**normal Python class**_

## Create a schema
## Create an instance of the mapped class
## Creating a session
We’re now ready to start talking to the database. The ORM’s “handle” to the database is the Session. 
> **Session lifecycle patterns**  
>  ... think of an application thread as a guest at a dinner party, the Session is the guest’s plate and the objects
> it holds are the food (and the database…the kitchen?)!   
> See more on [THIS PAGE](https://docs.sqlalchemy.org/en/13/orm/session_basics.html#session-faq-whentocreate)

###### When do I construct a Session, when do I commit it, and when do I close it?
> The basic rules:
> 1. As a general rule, keep the lifecycle of the session _**separate and external**_ from 
>functions and objects that access and/or manipulate database data. This will greatly 
>help with achieving a predictable and consistent transactional scope.
> 2. Make sure you have a clear notion of where transactions begin and end, and **_keep_** 
>**_transactions short_**, meaning, they end at the series of a sequence of operations, 
>instead of being held open indefinitely.













---
---
\*\* OVERALL TIPS(not in tutorial)
- sqlAlchemy的session的类型:
```
sqlalchemy.orm.session.Session
```
- sqlalchemy的Update:
```
session.query(model_class).filter(model_class.UserId == user_id).\
		      update({model_class.UserPW: hashed_user_pwd})
```
