from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

@app.post("/analyze")
async def analyze(request: Request):
    body = await request.body()
    length = len(body)
    sentiment = "positive" if length % 3 == 0 else ("neutral" if length % 3 == 1 else "negative")
    keywords = ["activity", "feedback"]
    return JSONResponse({"sentiment": sentiment, "keywords": keywords})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
