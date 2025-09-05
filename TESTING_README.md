# SyriaGPT API Endpoint Testing Framework

A comprehensive testing framework for all SyriaGPT API endpoints with structured logging and detailed reporting.

## 🚀 Quick Start

### Option 1: Simple Testing (Recommended for beginners)
```bash
# Windows
run_tests.bat

# Linux/Mac
python run_tests_simple.py
```

### Option 2: Advanced Testing
```bash
# Install requirements
pip install -r test_requirements.txt

# Run with default settings
python run_tests.py

# Run with custom options
python run_tests.py --base-url http://localhost:8000 --verbose
```

## 📋 Features

- **Comprehensive Coverage**: Tests all API endpoints across all modules
- **Structured Logging**: Detailed JSON logs with performance metrics
- **Error Analysis**: Categorizes and analyzes test failures
- **Performance Monitoring**: Tracks response times and identifies slow endpoints
- **Coverage Reporting**: Shows which endpoints were tested and their success rates
- **Automatic Cleanup**: Removes test data after testing (configurable)
- **Multiple Output Formats**: Console output + detailed JSON reports

## 🧪 Test Coverage

The framework tests the following endpoint groups:

### 1. Health & System Endpoints
- `GET /test/health` - Health check
- `GET /health` - System health
- `GET /version` - API version
- `GET /system/info` - System information

### 2. Authentication Endpoints
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user
- `GET /auth/oauth/providers` - OAuth providers
- `POST /auth/forgot-password` - Password reset

### 3. User Management Endpoints
- `GET /users/me/profile` - Get user profile
- `PUT /users/me/profile` - Update profile
- `GET /users/me/settings` - Get user settings
- `GET /users/stats` - User statistics
- `GET /users/` - Search users (admin)
- `POST /users/me/change-password` - Change password

### 4. Questions Endpoints
- `GET /questions/` - Get all questions
- `POST /questions/` - Create question
- `GET /questions/{id}` - Get specific question
- `PUT /questions/{id}` - Update question
- `DELETE /questions/{id}` - Delete question

### 5. Answers Endpoints
- `GET /answers/` - Get all answers
- `POST /answers/` - Create answer
- `GET /questions/{id}/answers` - Get answers by question
- `PUT /answers/{id}` - Update answer
- `DELETE /answers/{id}` - Delete answer

### 6. Chat Management Endpoints
- `GET /chat/` - Get all chats
- `POST /chat/` - Create chat
- `GET /chat/{id}` - Get specific chat
- `PUT /chat/{id}` - Update chat
- `POST /chat/{id}/messages` - Send message
- `GET /chat/{id}/messages` - Get chat messages
- `DELETE /chat/{id}` - Delete chat

### 7. Intelligent Q&A Endpoints
- `POST /intelligent-qa/ask` - Ask AI question
- `POST /intelligent-qa/augment-variants` - Generate question variants

### 8. Session Management Endpoints
- `GET /sessions/` - Get user sessions
- `POST /sessions/` - Create session
- `GET /sessions/{id}` - Get specific session
- `PUT /sessions/{id}` - Update session
- `POST /sessions/logout` - Logout session
- `DELETE /sessions/{id}` - Delete session

### 9. SMTP Configuration Endpoints
- `GET /smtp/providers` - Get SMTP providers
- `GET /smtp/providers/{provider}` - Get specific provider
- `GET /smtp/health` - SMTP health check
- `POST /smtp/test` - Test SMTP connection

## 📊 Output and Reports

### Console Output
The framework provides real-time console output showing:
- ✅/❌ Test status indicators
- Response times with performance indicators (⚡ FAST, ⚠️ SLOW, 🐌 CRITICAL)
- Error messages for failed tests
- Summary statistics

### JSON Reports
Detailed JSON reports are saved to the `test_results/` directory with:
- Complete test results with request/response data
- Performance analysis and metrics
- Error categorization and analysis
- Endpoint coverage statistics
- Test metadata and configuration

### Log Files
Structured log files are created with:
- Timestamped test execution logs
- Error details and stack traces
- Performance metrics
- Configuration information

## ⚙️ Configuration

### Environment Variables
```bash
# API Configuration
export API_BASE_URL="http://localhost:8000"
export API_TIMEOUT="30"
export API_MAX_RETRIES="3"

# Test Configuration
export TEST_LOG_LEVEL="INFO"
export TEST_OUTPUT_DIR="test_results"
export SAVE_DETAILED_LOGS="true"
export SKIP_CLEANUP="false"
export PARALLEL_TESTS="false"
```

### Test Configuration File
Edit `test_config.py` to customize:
- Base URL and timeout settings
- Test data generation
- Performance thresholds
- Enabled test groups
- Output directory

## 🎯 Command Line Options

### Advanced Runner (`run_tests.py`)
```bash
python run_tests.py [OPTIONS]

Options:
  --base-url URL        Base URL for API testing (default: http://localhost:8000)
  --output-dir DIR      Output directory for results (default: test_results)
  --skip-cleanup        Skip cleanup of test data
  --groups GROUP [GROUP ...]  Specific test groups to run
  --verbose, -v         Verbose logging
  --help               Show help message
```

### Examples
```bash
# Test only authentication and user management
python run_tests.py --groups authentication user_management

# Test with verbose logging and custom output directory
python run_tests.py --verbose --output-dir my_test_results

# Test against staging environment
python run_tests.py --base-url https://staging.syriagpt.com

# Skip cleanup for debugging
python run_tests.py --skip-cleanup
```

## 📈 Performance Thresholds

The framework includes configurable performance thresholds:

- **Fast**: < 100ms (⚡ indicator)
- **Normal**: 100ms - 2s
- **Slow**: 2s - 5s (⚠️ indicator)
- **Critical**: > 5s (🐌 indicator)

## 🔧 Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure the API server is running
   - Check the base URL in configuration
   - Verify firewall settings

2. **Authentication Failures**
   - Check if test user registration is working
   - Verify JWT token generation
   - Ensure database is accessible

3. **Timeout Errors**
   - Increase timeout in configuration
   - Check server performance
   - Verify network connectivity

4. **Test Data Cleanup Issues**
   - Use `--skip-cleanup` to debug
   - Check database permissions
   - Verify foreign key constraints

### Debug Mode
```bash
# Run with maximum verbosity
python run_tests.py --verbose --skip-cleanup

# Check log files in the output directory
tail -f test_results/api_test_*.log
```

## 📁 File Structure

```
├── test_endpoints.py          # Core testing framework
├── run_tests.py              # Advanced test runner
├── run_tests_simple.py       # Simple test runner
├── run_tests.bat             # Windows batch file
├── test_config.py            # Configuration settings
├── test_requirements.txt     # Python dependencies
├── TESTING_README.md         # This documentation
└── test_results/             # Output directory
    ├── enhanced_api_test_results_*.json
    ├── api_test_results_*.json
    └── api_test_*.log
```

## 🚀 Integration

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Run API Tests
  run: |
    pip install -r test_requirements.txt
    python run_tests.py --base-url ${{ env.API_URL }}
```

### Docker Integration
```dockerfile
# Add to your Dockerfile
COPY test_*.py test_config.py test_requirements.txt ./
RUN pip install -r test_requirements.txt
CMD ["python", "run_tests_simple.py"]
```

## 📝 Contributing

To add new test cases:

1. **Add new endpoint tests** in `test_endpoints.py`
2. **Update configuration** in `test_config.py` if needed
3. **Add test data generators** for new endpoint types
4. **Update documentation** with new endpoint coverage

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review log files for detailed error information
3. Ensure all dependencies are installed
4. Verify API server is running and accessible

---

**Happy Testing! 🧪✨**
