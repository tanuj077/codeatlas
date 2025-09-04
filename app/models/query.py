from pydantic import BaseModel

class SearchResponseItem(BaseModel):
    score: float
    path: str
    name: str
    type: str
    start_line: int
    end_line: int

class SearchResponse(BaseModel):
    results: list[SearchResponseItem]

