# Testing Guide

This document provides comprehensive information about running and maintaining tests for the Manga Reader application.

## Overview

The project includes comprehensive test coverage across multiple layers:

- **Backend Tests** (Python/FastAPI)
  - Unit tests for models, services, and utilities
  - API endpoint tests
  - Integration tests
  - Security tests

- **Frontend Tests** (Svelte/TypeScript)  
  - Component unit tests
  - Integration tests
  - End-to-end tests

## Backend Testing

### Prerequisites

Install test dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### Running Tests

#### Run All Tests
```bash
pytest
```

#### Run Tests by Category
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Authentication tests
pytest -m auth

# Manga functionality tests
pytest -m manga

# Image serving tests
pytest -m images

# Progress tracking tests
pytest -m progress
```

#### Run Tests with Coverage
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

#### Run Specific Test Files
```bash
# Test specific module
pytest tests/api/test_auth.py

# Test specific function
pytest tests/api/test_auth.py::TestAuthEndpoints::test_register_user

# Test with verbose output
pytest -v tests/models/test_models.py
```

### Test Structure

```
backend/tests/
├── conftest.py              # Test configuration and fixtures
├── api/                     # API endpoint tests
│   ├── test_auth.py
│   ├── test_manga.py
│   ├── test_images.py
│   └── test_progress.py
├── core/                    # Core functionality tests
│   └── test_security.py
├── models/                  # Database model tests
│   └── test_models.py
├── services/                # Business logic tests
│   └── test_manga_scanner.py
└── integration/             # Integration tests
    └── test_workflows.py
```

### Key Testing Features

- **Database Isolation**: Each test uses an in-memory SQLite database
- **Authentication Mocking**: Helper functions for creating authenticated clients
- **File System Mocking**: Temporary directories for testing file operations
- **API Client Testing**: Async HTTP client for endpoint testing
- **Comprehensive Fixtures**: Pre-configured test data (users, manga, chapters, pages)

## Frontend Testing

### Prerequisites

Install test dependencies:
```bash
cd frontend
npm install
```

### Running Tests

#### Unit Tests (Vitest)
```bash
# Run all unit tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

#### End-to-End Tests (Playwright)
```bash
# Install Playwright browsers
npx playwright install

# Run E2E tests
npm run test:e2e

# Run E2E tests in headed mode
npx playwright test --headed

# Run specific test file
npx playwright test tests/e2e/auth.spec.ts
```

### Test Structure

```
frontend/
├── vitest.config.ts         # Vitest configuration
├── playwright.config.ts     # Playwright configuration
├── src/
│   ├── tests/
│   │   └── setup.ts         # Test setup and mocks
│   └── lib/components/
│       ├── *.test.ts        # Component unit tests
│       └── *.svelte         # Components being tested
└── tests/
    └── e2e/
        └── *.spec.ts        # End-to-end tests
```

## Continuous Integration

### GitHub Actions Workflow

The project includes automated testing via GitHub Actions:

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run backend tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run unit tests
        run: |
          cd frontend
          npm run test:coverage
      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright install --with-deps
          npm run test:e2e
```

## Test Data Management

### Backend Test Data

The backend uses fixtures to create consistent test data:

```python
# Pre-configured test data available in all tests
@pytest.fixture
async def test_user(test_db): ...          # Creates user with preferences

@pytest.fixture  
async def test_manga(test_db): ...         # Creates manga with chapters and pages

@pytest.fixture
def temp_manga_dir(): ...                 # Creates temporary manga directory structure
```

### Frontend Test Data

Frontend tests use mocked API responses:

```typescript
// Mock API responses for consistent testing
const mockManga = [
  {
    id: 1,
    title: 'One Piece',
    slug: 'one-piece',
    // ...
  }
];
```

## Coverage Requirements

### Target Coverage Levels

- **Backend**: Minimum 85% code coverage
  - Models: 90%+
  - API endpoints: 90%+
  - Services: 85%+
  - Security functions: 95%+

- **Frontend**: Minimum 80% code coverage
  - Components: 85%+
  - Utilities: 90%+
  - Stores: 85%+

### Coverage Reports

#### Backend Coverage
```bash
cd backend
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

#### Frontend Coverage
```bash
cd frontend
npm run test:coverage
# Open coverage/index.html in browser
```

## Performance Testing

### Backend Performance Tests

Some integration tests include performance validation:

```python
@pytest.mark.slow
async def test_large_manga_library_performance():
    # Test with 100+ manga entries
    # Ensure pagination performs well
```

### Frontend Performance Tests  

E2E tests include performance checks:

```typescript
test('should load manga library quickly', async ({ page }) => {
  const startTime = Date.now();
  await page.goto('/');
  await expect(page.locator('[data-testid="manga-grid"]')).toBeVisible();
  const loadTime = Date.now() - startTime;
  expect(loadTime).toBeLessThan(3000);
});
```

## Debugging Tests

### Backend Debugging

```bash
# Run tests with debugging output
pytest -v -s tests/api/test_auth.py

# Run single test with pdb
pytest --pdb tests/api/test_auth.py::test_specific_function

# Run with logging
pytest --log-cli-level=DEBUG
```

### Frontend Debugging

```bash
# Run Vitest in debug mode
npm run test -- --reporter=verbose

# Run Playwright in debug mode
npx playwright test --debug

# Run with browser visible
npx playwright test --headed --slowmo=1000
```

## Test Environment Setup

### Environment Variables

Create `.env.test` files for test-specific configuration:

```bash
# backend/.env.test
DATABASE_URL=sqlite:///test.db
SECRET_KEY=test_secret_key_for_testing_only
ACCESS_TOKEN_EXPIRE_MINUTES=30

# frontend/.env.test
VITE_API_URL=http://localhost:8000
VITE_APP_ENV=test
```

### Docker Testing

For isolated testing environments:

```bash
# Run backend tests in Docker
docker-compose -f docker-compose.test.yml up --build backend-tests

# Run frontend tests in Docker  
docker-compose -f docker-compose.test.yml up --build frontend-tests
```

## Writing New Tests

### Backend Test Guidelines

1. **Use appropriate markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, etc.
2. **Use fixtures**: Leverage existing fixtures for common test data
3. **Test edge cases**: Include error conditions and boundary values
4. **Mock external dependencies**: Use `unittest.mock` for external services
5. **Async/await**: Properly handle async operations

Example:
```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_manga(test_db: AsyncSession):
    manga = Manga(title="Test", slug="test", folder_path="/test")
    test_db.add(manga)
    await test_db.commit()
    assert manga.id is not None
```

### Frontend Test Guidelines

1. **Use Testing Library**: Prefer `@testing-library/svelte` queries
2. **Test user interactions**: Focus on user behavior, not implementation
3. **Mock external dependencies**: Mock API calls and navigation
4. **Accessibility**: Include accessibility assertions
5. **Responsive testing**: Test different viewport sizes

Example:
```typescript
test('should handle user input', async () => {
  const { component } = render(SearchBar);
  const mockSearch = vi.fn();
  component.$on('search', mockSearch);
  
  const input = screen.getByPlaceholderText('Search manga...');
  await user.type(input, 'One Piece');
  
  expect(mockSearch).toHaveBeenCalledWith(
    expect.objectContaining({ detail: 'One Piece' })
  );
});
```

## Troubleshooting

### Common Issues

#### Backend
- **Import errors**: Ensure PYTHONPATH includes the app directory
- **Database connection errors**: Check test database configuration
- **Async test failures**: Ensure proper use of `@pytest.mark.asyncio`

#### Frontend
- **Module not found**: Run `npm install` to ensure dependencies are installed
- **Browser crashes in E2E**: Install browsers with `npx playwright install`
- **Component import errors**: Check file paths and Svelte configuration

### Getting Help

- Check existing test examples in the codebase
- Review test output for detailed error messages
- Use debugger breakpoints for complex test failures
- Refer to official documentation:
  - [Pytest](https://docs.pytest.org/)
  - [Vitest](https://vitest.dev/)
  - [Playwright](https://playwright.dev/)
  - [Testing Library](https://testing-library.com/)

## Contributing

When adding new features:

1. **Write tests first** (TDD approach recommended)
2. **Maintain coverage**: Ensure new code is properly tested
3. **Update documentation**: Include test instructions for new features
4. **Run full test suite**: Verify no regressions before submitting PRs

### Pre-commit Hooks

Consider setting up pre-commit hooks to run tests automatically:

```bash
# Install pre-commit
pip install pre-commit

# Set up git hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```