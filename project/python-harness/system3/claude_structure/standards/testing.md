# Testing Standards

## Test Organization

1. **File structure**:
   - One test file per source module
   - Name: `test_{module_name}.py`
   - Group tests into classes by functionality

2. **Test naming**:
   - Use descriptive names: `test_route_claim_tier_1_approved`
   - Start with `test_`
   - Include expected behavior in name

## Pytest Best Practices

1. **Fixtures**:
   - Use fixtures for common setup
   - Scope appropriately (function, class, module)
   - Keep fixtures simple

2. **Assertions**:
   - Use specific assertions
   - Include helpful failure messages
   - Test one thing per test
