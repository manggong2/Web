from fastapi import FastAPI

import requests

app = FastAPI()

@app.get("/")
def root():
    URL = "https://bigdata.kepco.co.kr/openapi/v1/powerUsage/industryType.do?year=2023&month=12&apiKey=34cuFl36WbAEE5JClbnupw2A3oS7qW7f1i15II5D&returnType=json"

    contents = requests.get(URL).text

    return { "message": contents }

@app.get("/home")
def home():
    return { "message": "Home!" } 