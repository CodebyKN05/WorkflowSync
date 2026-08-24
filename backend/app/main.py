from fastapi import FastAPI

app = FastAPI(title="WorkflowSync API")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "WorkflowSync backend is running"}
