from pydantic import BaseModel

class FeedbackCreate(BaseModel):
    user_name: str
    comments: str
    rating: int