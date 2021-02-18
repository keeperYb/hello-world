跳过章节标记: SKIPPED     
书签标记: _BOOKMARK     
更改md标记: TODO NOW

# FastAPI learning Note
## CHAPTER: First Steps

### Recap, step by step
- Step 1: import FastAPI ...
- Step 2: create FastAPI 'instance'
``` python
from fastapi import FastAPI

app = FastAPI()  # object 'app' is an instance of class FastAPI
```
- Step 3: create a path operation 
- Step 4: define the path operation function: in this example, root()
```python
async def root():
    return {"message": "Hello World"}
```

---
---
   
   
## CHAPTER: Path Parameters
###
```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/items/{item_id}")
async def read_item(item_id):
    return {"item_id": item_id}
```

### Data Conversion
With the same Python type declaration(int here), FastAPI gives you data validation.
```python
async def read_item(item_id: int):  
    # do sth
    pass
```

### Order Matters for path parameters
order matters, specific one should be declared BEFORE common one,
in the following example, '/users/me' should be declared before '/users/{user_id}'
```python
@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}
```

### Predefined values
Work with an enum as the predefined value  
### Path parameters containing paths
Recursion... using path converter from Starlette, like this: 
```
/files/{file_path:path}
```  
the last part, :path, tells it that the parameter should match any path


---
---
## CHAPTER: Query Parameters
other parameters that are not part of the path parameters, they are 'query' parameters
```python
from fastapi import FastAPI
app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
```
The query is the set of key-value pairs that go after the ? in a URL, separated by & characters.
For example, in the URL:
http://127.0.0.1:8000/items/?skip=0&limit=10

### Defaults
```python
from fastapi import FastAPI

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


@app.get("/items/")
# skip = 0 , limit = 10 is the default parameter
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
```


### Optional Parameters
parameter can be set to None, like this:
```python
from typing import Optional  # import typing.Optional
from fastapi import FastAPI

app = FastAPI()


@app.get("/items/{item_id}")
async def read_item(item_id: str, q: Optional[str] = None):  # setting to None
    if q:
        return {"item_id": item_id, "q": q}
    return {"item_id": item_id}

```


### Query parameter type conversion


## CHAPTER: Request Body
the client sends 'request body', the server returns 'response body'
To declare a request body, you use \_\_Pydantic\_\_ models with all their power and benefits.  

Pydantic 是用来定义model的  
- Import Pydantic's BaseModel
- Create your data model
- Declare it as a parameter  
- Results  
- Automatic Docs  
- Editor Support  
> Tips:  
> You get editor support if you use Pydantic model, instead of 'dict'

- Use the model  
- Request body + path + query parameters  

---
---
## CHAPTER: Query Parameters and String Validations  
TODO NOW  
.
.SKIPPED
.

Request Files==============================
Import File------------------------------
from fastapi import FastAPI, File, UploadFile

Define File parameters------------------------------
# file: bytes will be stored in MEMORY, means it's suitable for small files, while...

File parameters with UploadFile------------------------------
# file: UploadFile , exposes a SpooledTemporaryFile object as a file-like object
	- UploadFile------------------------------
	# UploadFile has the following async methods. 
	# They all call the corresponding file methods underneath 
	# (using the internal SpooledTemporaryFile).
	
	# inside of an async path operation function you can get the contents with:
	# contents = await myfile.read()
	# while inside of a normal def path operation function, 
	# you can access the UploadFile.file directly, for example:
	# contents = myfile.file.read()



SQL(Relational) Databases==============================
ORMs------------------------------
File Structure------------------------------
.
└── sql_app
    ├── __init__.py
    ├── crud.py (details in 'CRUD utils')
    ├── database.py (details in 'Create the SQLAlchemy parts')
    ├── main.py
    ├── models.py (details in 'Create the database models')
    └── schemas.py (details in 'Create the Pydantic models')
Create the SQLAlchemy parts------------------------------
Steps:
-Import the SQLAlchemy parts
-Create a database URL for SQLAlchemy
-Create the SQLAlchemy engine
	Note: 
	-connect_args={"check_same_thread": False}
	-'we will make sure each request gets its OWN DATABASE CONNECTION SESSION in a dependency'
-Create a SessionLocal class
	-'We name it SessionLocal to distinguish it from the Session we are importing from SQLAlchemy.'
-Create a Base class

Create the database models------------------------------
Steps:
-Create SQLAlchemy models from the Base class
-Create model attributes/columns
-Create the relationships
	# Critical! code like:
	from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
	from sqlalchemy.orm import relationship

	from .database import Base


	class User(Base):
		__tablename__ = "users"

		id = Column(Integer, primary_key=True, index=True)
		email = Column(String, unique=True, index=True)
		hashed_password = Column(String)
		is_active = Column(Boolean, default=True)

		items = relationship("Item", back_populates="owner") # relation...


	class Item(Base):
		__tablename__ = "items"

		id = Column(Integer, primary_key=True, index=True)
		title = Column(String, index=True)
		description = Column(String, index=True)
		owner_id = Column(Integer, ForeignKey("users.id"))

		owner = relationship("User", back_populates="items") # relation...

Create the Pydantic models------------------------------
Steps:
-Create initial Pydantic models/schemas ?? 
	# Class ItemCreate ? >> see comments BELOW
	-SQLAlchemy style and Pydantic style
-Create Pydantic models/schemas for reading/returning
	# Class Item , maybe means 'ItemRead'... corresponding to 'ItemCreate'
-Use Pydantic's orm_mode
	# add an internal Config class in class : Item and User.
	# the Config class is used to provide configurations to Pydantic
	# Without orm_mode, if you returned a SQLAlchemy model from your path operation, it wouldn't include the relationship data.

CRUD utils------------------------------
 # steps of create a SQLAlchemy model instance with some data:
 #	- add that instance object to your database session.
 #	- commit the changes to the database (so that they are saved).
 #	-* REFRESH your instance (so that it contains any new data from the database, like the generated ID).

## Static Files
### Install aiofiles ...
### Use StaticFiles
```python
from fastapi import FastAPI  # Import StaticFiles.
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# "Mount" a StaticFiles() instance in a specific path.
app.mount("/static", StaticFiles(directory="static"), name="static")  # for more details, check 'Details' section below
```
> What is mounting?  
>"Mounting" means adding a complete "independent" application in a specific path, that then takes care of handling all 
>the sub-paths.
>
>This is different from using an APIRouter as a mounted application is completely independent. The OpenAPI and docs from 
>your main application won't include anything from the mounted application, etc.

### Details
The first "/static" refers to the sub-path this "sub-application" will be "mounted" on. So, any path that starts with 
"/static" will be handled by it.

The directory="static" refers to the name of the directory that contains your static files.

The name="static" gives it a name that can be used internally by FastAPI.

All these parameters can be different than "static", adjust them with the needs and specific details of your own 
application.


















