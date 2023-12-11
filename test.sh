curl -X POST -H "Content-Type: application/json" -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
        {
            "role": "user",
            "content": "What can you do"
        }
    ]
}' localhost:8000/v1/chat/completions