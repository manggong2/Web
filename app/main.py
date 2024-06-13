from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import requests
import xmltodict
import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
import pandas as pd

library = '/code/data/도서관정보나루_참여도서관목록.xlsx'
LIBRARY_CODE = ""

# 엑셀 파일을 읽어옵니다.
try:
    df = pd.read_excel(library, engine='openpyxl')
    results = pd.DataFrame()
except Exception as e:
    print(f"엑셀 파일을 읽는 중 오류가 발생했습니다: {e}")
    df = pd.DataFrame()  # 에러 발생 시 빈 데이터프레임으로 초기화

SQLALCHEMY_DATABASE_URL = "sqlite:///../bookmark.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

app = FastAPI()

# Static and template directories
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

NAVER_CLIENT_ID = "mqw55g68zcYsPz010T6X"
NAVER_CLIENT_SECRET = "hsMn6N5zrC"
LIBRARY_API_KEY = "3e5fb0211ccb689a197c05a8d9fbe77e149314ec1beb34f4edbd11489fb647c3"

# 상태 저장소
class BookStore:
    def __init__(self):
        self.books: List[Dict[str, Any]] = []

book_store = BookStore()

# 북마크 기능
class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    link = Column(String)
    image = Column(String)
    author = Column(String)
    price = Column(String)
    isbn = Column(String)
    description = Column(String)

Base.metadata.create_all(bind=engine)

class BookmarkCreate(BaseModel):
    title: str
    link: str
    image: str
    author: str
    price: str
    isbn: str
    description: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("search_library.html", {"request": request})

@app.get("/libraries", response_class=JSONResponse)
def search_libraries(query: str):
    """
    도서관 이름을 검색합니다.
    """
    global results
    libraries = []
    if query:
        results = df[df['도서관명'].str.contains(query, case=False, na=False)]
        if not results.empty:
            libraries = results[['도서관명', '도서관코드']].to_dict(orient='records')
        else:
            raise HTTPException(status_code=404, detail="일치하는 도서관을 찾을 수 없습니다.")
    return libraries

@app.post("/library_code/{index}", response_class=JSONResponse)
def get_library_code_by_index(index: int):
    global LIBRARY_CODE
    """
    도서관 목록에서 인덱스로 도서관 코드를 조회합니다.
    """
    try:
        LIBRARY_CODE = results.iloc[index]['도서관코드']
        return {"message": "Library code has been successfully set."}
    except IndexError:
        raise HTTPException(status_code=404, detail="유효하지 않은 인덱스입니다.")

@app.get("/books", response_class=JSONResponse)
def search_books(query: str, store: BookStore = Depends(lambda: book_store)):
    """
    사용자가 제공한 쿼리를 바탕으로 Naver에서 책을 검색합니다.
    """
    naver_url = f"https://openapi.naver.com/v1/search/book.json?query={query}&display=10&start=1"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }

    res = requests.get(naver_url, headers=headers)
    
    if res.status_code == 200:
        books = res.json().get('items', [])
        if not books:
            return {"error": "No books found"}
        # 검색된 책들을 상태 저장소에 저장
        store.books = books
        return books
    else:
        raise HTTPException(status_code=res.status_code, detail="Naver API request failed")

@app.post("/check/{index}", response_class=JSONResponse)
def check_availability(index: int, store: BookStore = Depends(lambda: book_store)):
    global LIBRARY_CODE
    if index < 0 or index >= len(store.books):
        raise HTTPException(status_code=400, detail="Invalid book index")

    # 해당 책의 ISBN을 추출합니다.
    isbn = store.books[index].get('isbn')
    if not isbn:
        return {"error": "No ISBN found for the selected book"}

    # ISBN에서 13자 값을 추출합니다.
    isbn13 = isbn.split()[-1]
    
    # 도서관 API에 ISBN13을 사용해 요청을 보냅니다.
    library_url = f"http://data4library.kr/api/bookExist?authKey={LIBRARY_API_KEY}&libCode={LIBRARY_CODE}&isbn13={isbn13}"
    library_res = requests.get(library_url)
    
    if library_res.status_code == 200:
        # XML 응답을 JSON으로 변환합니다.
        library_data = xmltodict.parse(library_res.content)
        result = json.loads(json.dumps(library_data))
        has_book = result.get('response', {}).get('result', {}).get('hasBook', 'No information available')
        loan_available = result.get('response', {}).get('result', {}).get('loanAvailable', 'No information available')
        return {"hasBook": has_book, "loanAvailable": loan_available}
    else:
        raise HTTPException(status_code=library_res.status_code, detail="Library API request failed")

@app.post("/bookmark/{index}", response_class=JSONResponse)
def toggle_bookmark(index: int, store: BookStore = Depends(lambda: book_store), db: Session = Depends(get_db)):
    """
    특정 인덱스의 책을 북마크하거나 북마크를 삭제합니다.
    """
    if index < 0 or index >= len(store.books):
        raise HTTPException(status_code=400, detail="Invalid book index")
    
    book = store.books[index]
    db_bookmark = db.query(Bookmark).filter_by(title=book['title']).first()
    
    if db_bookmark:
        # 이미 북마크된 책이면 삭제
        db.delete(db_bookmark)
        db.commit()
        return {"message": "Bookmark removed"}
    else:
        # 북마크되지 않은 책이면 추가
        db_bookmark = Bookmark(
            title=book['title'],
            link=book['link'],
            image=book['image'],
            author=book['author'],
            price=book['discount'],
            isbn=book['isbn'],
            description=book['description'],
        )
        db.add(db_bookmark)
        db.commit()
        db.refresh(db_bookmark)
        return {"message": "Bookmarked successfully"}