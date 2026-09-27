from fastapi import FastAPI

app = FastAPI()

@app.get("/login")
async def read_users():
    return [{"username": "user1"}, {"username": "user2"}]