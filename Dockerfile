services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - DASHSCOPE_BASE_URL=${DASHSCOPE_BASE_URL:-https://dashscope.aliyuncs.com/compatible-mode/v1}
      - DATABASE_URL=${DATABASE_URL:-sqlite:////app/app.db}
 
