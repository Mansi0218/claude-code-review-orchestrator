# API Design Standards

## REST API Guidelines

1. **Use proper HTTP methods**:
   - GET for retrieval
   - POST for creation
   - PUT/PATCH for updates
   - DELETE for removal

2. **Response codes**:
   - 200 OK for successful GET
   - 201 Created for successful POST
   - 204 No Content for successful DELETE
   - 400 Bad Request for client errors
   - 500 Internal Server Error for server errors

## Claude API Integration

1. **Model selection**:
   - Use Claude 3.5 Sonnet for production
   - Set appropriate max_tokens
   - Include system prompts when needed

2. **Error handling**:
   - Catch API exceptions
   - Implement retry logic for transient failures
   - Log all API errors
