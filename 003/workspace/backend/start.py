#!/usr/bin/env python3
import uvicorn
uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
