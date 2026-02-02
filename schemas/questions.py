from pydantic import BaseModel


class QuestionCreate(BaseModel):
    content: str

    class Config:
        min_anystr_length = 1
        max_anystr_length = 1000
