from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

user_name = None

class User(BaseModel):
    name: str


@app.get("/")
def root():
    return{ "message": "Hello yejini!"}

@app.get("/home")
def home():
    return { "message": "Bye yejini!" }

#####여기까지 저번주########


@app.post("/user/")
async def receive_user(user: User):
    global user_name
    user_name = user.name
    return {"message": "User name received"}


@app.get("/user/")
async def get_user():
    return {"user_name": user_name}

@app.put("/user/")
async def receive_user(user: User):
    global user_name
    user_name = user.name
    return {"message": "User name changed"}


@app.delete("/user/")
async def del_user():
    global user_name
    user_name = "DELETED"
    return {"message": "User name deleted"}


######

# 클래스 쓰는 법

user1=User(name="yejini hihi")



###########