from fastapi import FastAPI
import requests
import xml.etree.ElementTree as ET

app = FastAPI()

@app.get("/")
def root():
    URL = "https://openapi.naver.com/v1/search/book.xml?query=%EC%A3%BC%EC%8B%9D&display=10&start=1"
    headers = {
        "X-Naver-Client-Id": "mqw55g68zcYsPz010T6X",
        "X-Naver-Client-Secret": "hsMn6N5zrC"
    }

    res = requests.get(URL, headers=headers)
    if res.status_code == 200:
        # XML 파싱
        root = ET.fromstring(res.content)
        isbn_list = []
        for item in root.findall(".//item"):
            isbn = item.find("isbn")
            if isbn is not None:
                isbn_list.append(isbn.text)
        return {"isbn_list": isbn_list}
    else:
        return {"error": "Request failed with status code " + str(res.status_code)}

@app.get("/home")
def home():
    return {"message": "Home!"}
