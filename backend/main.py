from fastapi import FastAPI

app = FastAPI(title="ICT Trading Signal Platform API")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ict-signal-platform-backend"}