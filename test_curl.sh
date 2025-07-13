#!/bin/bash
# Test Tenbin OpenAI API using curl commands

API_BASE="http://127.0.0.1:8401"
API_KEY="sk-dummy-3e5010a20e8f4832a5f213ee85e6a3c7"

echo "=== Testing Tenbin OpenAI API with curl ==="
echo

echo "1. Testing /models endpoint (no auth):"
curl -s "$API_BASE/models" | jq '.data[0:3]'
echo

echo "2. Testing /v1/models endpoint (with auth):"
curl -s -H "Authorization: Bearer $API_KEY" "$API_BASE/v1/models" | jq '.data[0:3]'
echo

echo "3. Testing chat completion (streaming):"
curl -s -X POST "$API_BASE/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "Claude-3.5-Sonnet",
    "messages": [
      {"role": "user", "content": "What is 2+2? Give a brief answer."}
    ],
    "stream": true,
    "max_tokens": 50
  }' --no-buffer
echo

echo "4. Testing chat completion (non-streaming):"
curl -s -X POST "$API_BASE/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "Claude-3.5-Sonnet",
    "messages": [
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "stream": false,
    "max_tokens": 50
  }' | jq '.choices[0].message.content'
echo

echo "=== Tests completed ==="