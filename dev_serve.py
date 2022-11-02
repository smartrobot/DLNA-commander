import uvicorn

if __name__ == '__main__':
    uvicorn.run("app.main:app", port=5000, reload=True, host="0.0.0.0")