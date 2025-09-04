from fastapi import FastAPI
from app.api import search, chat, repos
from scripts.init_db import init_repos
import dotenv

dotenv.load_dotenv()

# Run init pipeline before FastAPI is created
init_repos()

app = FastAPI()
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(repos.router, prefix="/repos", tags=["Repos"])


@app.get("/")
def root():
    return {"message": "CodeAtlas API running"}
