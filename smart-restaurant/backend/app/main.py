from fastapi import FastAPI

# Creates the API application served by Uvicorn.
app = FastAPI(title="Smart Restaurant API")


@app.get("/health")
def health():
    """Reports that the backend process is responding."""
    return {"status": "ok"}