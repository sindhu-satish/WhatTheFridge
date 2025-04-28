#!/bin/bash
npm run build && uvicorn app:app --host 0.0.0.0 --port $PORT 