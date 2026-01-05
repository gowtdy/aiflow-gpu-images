#/bin/sh

echo "Testing mtserver"
curl -X POST http://localhost:5400/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{ \
    "model": "mt-model", \
    "messages": [ \
        { \
          "role": "system", \
          "content": [{"type": "text", "text": "You are a helpful assistant."}] \
        }, \
        { \
          "role": "user", \
          "content": [{"type": "text", "text": "您今天在想什么?"}] \
        } \
    ], \
    "max_tokens": 2048, \
    "temperature": 0.7, \
    "top_p": 0.6, \
    "top_k": 20, \
    "repetition_penalty": 1.05, \
    "stop_tokens_ids": [127960] \
  }'
