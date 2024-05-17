from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/")
def root():
    URL = "https://openapi.naver.com/v1/search/book.json?query=%EC%A3%BC%EC%8B%9D&display=10&start=1"
    headers = {
        "X-Naver-Client-Id": "mqw55g68zcYsPz010T6X",
        "X-Naver-Client-Secret": "hsMn6N5zrC"
    }

    res = requests.get(URL, headers=headers)
    print(res.status_code)
    if res.status_code == 200:
        return res.text
    else:
        return {"error": "Request failed with status code " + str(res.status_code)}

@app.get("/home")
def home():
    return {"message": "Home!"}
