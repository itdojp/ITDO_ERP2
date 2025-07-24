# Performance Testing Suite for ITDO ERP

This directory contains comprehensive performance testing tools and scripts for the ITDO ERP system using k6 load testing framework.

## 🎯 Overview

The performance testing suite provides:
- **Load Testing**: Realistic user load simulation
- **Stress Testing**: System breaking point identification  
- **Smoke Testing**: Quick API validation
- **Spike Testing**: Traffic surge handling
- **Regression Testing**: Performance baseline comparison

## 📁 Directory Structure

```
performance-testing/
├── scripts/
│   ├── load-test.js       # Main load testing scenarios
│   └── stress-test.js     # High-load stress testing
├── scenarios/
│   └── api-smoke-test.js  # Quick API validation
├── configs/
│   └── test-config.json   # Test configuration settings
├── reports/               # Generated test reports (auto-created)
├── run-tests.sh          # Test runner script
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Install k6**:
   ```bash
   # Linux
   curl https://github.com/grafana/k6/releases/download/v0.46.0/k6-v0.46.0-linux-amd64.tar.gz -L | tar xvz --strip-components 1
   
   # macOS
   brew install k6
   
   # Windows
   choco install k6
   ```

2. **Ensure target application is running**:
   ```bash
   # Local development
   cd backend && uv run uvicorn app.main:app --reload
   ```

### Running Tests

1. **Quick API validation** (2 minutes):
   ```bash
   ./run-tests.sh smoke
   ```

2. **Standard load test** (16 minutes):
   ```bash
   ./run-tests.sh load
   ```

3. **Stress test** (16 minutes):
   ```bash
   ./run-tests.sh stress
   ```

4. **Traffic spike test** (5 minutes):
   ```bash
   ./run-tests.sh spike
   ```

5. **Run all tests**:
   ```bash
   ./run-tests.sh all
   ```

6. **Test against specific URL**:
   ```bash
   ./run-tests.sh load https://api.example.com
   ```

## 📊 Test Scenarios

### Smoke Test
- **Duration**: 2 minutes
- **Load**: 1 virtual user
- **Purpose**: Validate API accessibility and basic functionality
- **Thresholds**:
  - 95% of requests < 1000ms
  - Error rate < 1%

### Load Test
- **Duration**: 16 minutes
- **Load**: Ramps from 10 to 20 virtual users
- **Purpose**: Simulate realistic user traffic patterns
- **Scenarios**:
  - User authentication flow
  - Organization management operations
  - Task creation and retrieval
  - Department listing
- **Thresholds**:
  - 95% of requests < 2000ms
  - Error rate < 5%

### Stress Test
- **Duration**: 16 minutes
- **Load**: Ramps up to 300 virtual users
- **Purpose**: Find system breaking points and behavior under extreme load
- **Scenarios**:
  - Heavy read operations (concurrent API calls)
  - Write-heavy operations (resource creation)
  - Database stress queries
  - Burst request patterns
- **Thresholds**:
  - 99% of requests < 5000ms
  - Error rate < 20% (higher tolerance for stress conditions)

### Spike Test
- **Duration**: 5 minutes
- **Load**: Sudden spike from 10 to 100 users, then back down
- **Purpose**: Test system behavior under sudden traffic surges
- **Thresholds**:
  - 95% of requests < 3000ms
  - Error rate < 15%

## 📈 Metrics and Reports

### Generated Reports

Each test run generates:
- **JSON Report**: Detailed metrics data (`reports/test_YYYYMMDD_HHMMSS.json`)
- **HTML Report**: Visual performance dashboard (`reports/test_YYYYMMDD_HHMMSS.html`)
- **Summary Report**: Markdown summary with recommendations (`reports/summary_YYYYMMDD_HHMMSS.md`)

### Key Metrics

- **Response Time**:
  - Average response time
  - 95th percentile (p95)
  - 99th percentile (p99)
  
- **Throughput**:
  - Requests per second
  - Data transferred
  
- **Reliability**:
  - Error rate percentage
  - Timeout count
  - Success rate

- **Concurrency**:
  - Virtual users (VUs)
  - Peak concurrent users

## 🔧 Configuration

### Environment Variables

```bash
export BASE_URL="https://your-api.com"    # Target URL
export K6_OUT="json=results.json"         # Output format
export K6_QUIET="true"                     # Reduce output verbosity
```

### Test Configuration

Edit `configs/test-config.json` to customize:
- Test thresholds
- Environment URLs
- Reporting preferences
- Notification settings
- Regression testing parameters

### Custom Test Data

Modify test scripts to use your specific:
- User credentials
- Organization data
- API endpoints
- Test scenarios

## 🚨 Best Practices

### Before Testing

1. **Verify target environment**:
   - Ensure application is running
   - Database is properly initialized
   - All dependencies are available

2. **Resource monitoring**:
   - Monitor CPU, memory, and disk usage
   - Check database connection limits
   - Verify network capacity

3. **Test data preparation**:
   - Create test user accounts
   - Prepare test organizations/departments
   - Clean up previous test data

### During Testing

1. **Monitor system resources**:
   ```bash
   # Monitor system resources
   top -p $(pgrep -f "uvicorn\|python")
   
   # Monitor database connections
   psql -c "SELECT count(*) FROM pg_stat_activity;"
   
   # Monitor API logs
   tail -f logs/api.log
   ```

2. **Watch for alerts**:
   - High CPU/memory usage
   - Database connection exhaustion
   - Disk space issues
   - Network saturation

### After Testing

1. **Analyze results**:
   - Compare against baseline metrics
   - Identify performance bottlenecks
   - Check error logs for issues

2. **Clean up**:
   - Remove test data
   - Reset system state
   - Archive test reports

## 🎛️ Advanced Usage

### Custom Test Scenarios

Create custom test files:

```javascript
// custom-test.js
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 10,
  duration: '5m',
};

export default function() {
  const response = http.get('https://api.example.com/custom-endpoint');
  check(response, {
    'status is 200': (r) => r.status === 200,
  });
}
```

Run custom test:
```bash
k6 run --env BASE_URL="https://api.example.com" custom-test.js
```

### CI/CD Integration

Add to GitHub Actions workflow:

```yaml
- name: Run Performance Tests
  run: |
    cd performance-testing
    ./run-tests.sh smoke
    
- name: Upload Performance Reports
  uses: actions/upload-artifact@v4
  with:
    name: performance-reports
    path: performance-testing/reports/
```

### Continuous Performance Monitoring

Set up scheduled performance testing:

```bash
# Add to crontab for daily performance checks
0 2 * * * /path/to/performance-testing/run-tests.sh smoke > /var/log/perf-test.log 2>&1
```

## 🐛 Troubleshooting

### Common Issues

1. **"k6 not found"**:
   ```bash
   # Install k6 or add to PATH
   export PATH=$PATH:/path/to/k6
   ```

2. **"Target not accessible"**:
   ```bash
   # Check if application is running
   curl http://localhost:8000/health
   
   # Verify correct URL
   export BASE_URL="http://correct-url.com"
   ```

3. **"Connection refused"**:
   - Check if application is running on correct port
   - Verify firewall settings
   - Ensure database connections are available

4. **High error rates**:
   - Check application logs for errors
   - Monitor system resources
   - Reduce load or increase timeout values

### Debug Mode

Run tests with verbose output:

```bash
K6_QUIET=false ./run-tests.sh load
```

Enable debug logging:

```bash
export K6_LOG_LEVEL=debug
k6 run --log-level=debug scripts/load-test.js
```

## 📞 Support and Contributing

### Getting Help

1. Check application logs: `tail -f backend/logs/app.log`
2. Review k6 documentation: https://k6.io/docs/
3. Examine test reports in `reports/` directory

### Contributing

1. Add new test scenarios to `scenarios/` directory
2. Update configuration in `configs/test-config.json`
3. Enhance test runner script `run-tests.sh`
4. Update documentation

### Performance Baselines

Maintain performance baselines:

```bash
# Save baseline after successful test
cp reports/load_latest.json baselines/load_baseline.json

# Compare against baseline
k6 run --compare-to=baselines/load_baseline.json scripts/load-test.js
```

## 🎯 Performance Goals

### Target Metrics

- **Response Time**: 95% of requests < 2000ms
- **Error Rate**: < 1% under normal load
- **Throughput**: > 100 requests/second
- **Availability**: 99.9% uptime during testing
- **Scalability**: Linear performance up to 50 concurrent users

### Alerting Thresholds

- **Warning**: Response time > 1500ms (p95)
- **Critical**: Response time > 3000ms (p95)  
- **Warning**: Error rate > 2%
- **Critical**: Error rate > 5%