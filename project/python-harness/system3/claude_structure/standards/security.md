# Security Standards

## API Key Management

1. **Never commit secrets**:
   - Use environment variables
   - Add .env to .gitignore
   - Use secrets managers in production

2. **Key rotation**:
   - Rotate keys regularly
   - Have process for compromised keys
   - Use different keys for dev/prod

## Input Validation

1. **Validate all inputs**:
   - Use Pydantic models
   - Sanitize user input
   - Reject invalid data early

## Data Protection

1. **Sensitive data**:
   - Never log secrets or PII
   - Encrypt sensitive data at rest
   - Use HTTPS for transmission
