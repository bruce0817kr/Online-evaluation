const newman = require('newman');
const path = require('path');
const fs = require('fs');

// Test configuration
const TEST_CONFIG = {
  collection: path.join(__dirname, 'postman-collection.json'),
  environment: {
    name: 'Test Environment',
    values: [
      { key: 'baseUrl', value: process.env.BACKEND_URL || 'http://localhost:8080' },
      { key: 'authToken', value: '' },
      { key: 'templateId', value: '' },
      { key: 'evaluationId', value: '' },
      { key: 'projectId', value: 'test-project-id' },
      { key: 'companyId', value: 'test-company-id' }
    ]
  },
  reporters: ['cli', 'json', 'html'],
  reporterOptions: {
    json: {
      export: path.join(__dirname, 'reports', 'api-test-results.json')
    },
    html: {
      export: path.join(__dirname, 'reports', 'api-test-results.html'),
      template: path.join(__dirname, 'templates', 'custom-template.hbs')
    }
  }
};

// Performance metrics collector
class PerformanceCollector {
  constructor() {
    this.metrics = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      totalResponseTime: 0,
      maxResponseTime: 0,
      minResponseTime: Infinity,
      requestsByEndpoint: {},
      errorsByType: {}
    };
  }

  addRequest(request, response) {
    this.metrics.totalRequests++;
    
    if (response.code >= 200 && response.code < 300) {
      this.metrics.successfulRequests++;
    } else {
      this.metrics.failedRequests++;
      const errorType = `${response.code} ${response.status}`;
      this.metrics.errorsByType[errorType] = (this.metrics.errorsByType[errorType] || 0) + 1;
    }

    const responseTime = response.responseTime;
    this.metrics.totalResponseTime += responseTime;
    this.metrics.maxResponseTime = Math.max(this.metrics.maxResponseTime, responseTime);
    this.metrics.minResponseTime = Math.min(this.metrics.minResponseTime, responseTime);

    const endpoint = `${request.method} ${request.url.path.join('/')}`;
    if (!this.metrics.requestsByEndpoint[endpoint]) {
      this.metrics.requestsByEndpoint[endpoint] = {
        count: 0,
        totalTime: 0,
        avgTime: 0
      };
    }
    
    const endpointMetrics = this.metrics.requestsByEndpoint[endpoint];
    endpointMetrics.count++;
    endpointMetrics.totalTime += responseTime;
    endpointMetrics.avgTime = endpointMetrics.totalTime / endpointMetrics.count;
  }

  getReport() {
    return {
      ...this.metrics,
      avgResponseTime: this.metrics.totalResponseTime / this.metrics.totalRequests,
      successRate: (this.metrics.successfulRequests / this.metrics.totalRequests) * 100
    };
  }
}

// Custom test runner
function runAPITests(options = {}) {
  return new Promise((resolve, reject) => {
    const performanceCollector = new PerformanceCollector();
    const testResults = {
      passed: [],
      failed: [],
      skipped: []
    };

    // Ensure reports directory exists
    const reportsDir = path.join(__dirname, 'reports');
    if (!fs.existsSync(reportsDir)) {
      fs.mkdirSync(reportsDir, { recursive: true });
    }

    // Run collection
    const newmanRun = newman.run({
      collection: require(TEST_CONFIG.collection),
      environment: TEST_CONFIG.environment,
      reporters: TEST_CONFIG.reporters,
      reporterOptions: TEST_CONFIG.reporterOptions,
      insecure: true,
      timeout: 30000,
      timeoutRequest: 10000,
      ...options
    }, (err, summary) => {
      if (err) {
        reject(err);
        return;
      }

      // Generate comprehensive report
      const report = {
        summary: {
          totalTests: summary.run.stats.tests.total,
          passedTests: summary.run.stats.tests.pending,
          failedTests: summary.run.stats.tests.failed,
          totalAssertions: summary.run.stats.assertions.total,
          passedAssertions: summary.run.stats.assertions.pending,
          failedAssertions: summary.run.stats.assertions.failed,
          duration: summary.run.timings.completed - summary.run.timings.started
        },
        performance: performanceCollector.getReport(),
        testResults: testResults,
        timestamp: new Date().toISOString()
      };

      // Save comprehensive report
      fs.writeFileSync(
        path.join(reportsDir, 'comprehensive-api-report.json'),
        JSON.stringify(report, null, 2)
      );

      resolve(report);
    });

    // Event listeners
    newmanRun.on('request', (error, args) => {
      if (error) {
        console.error('Request error:', error);
        return;
      }
      performanceCollector.addRequest(args.request, args.response);
    });

    newmanRun.on('assertion', (error, args) => {
      const testInfo = {
        name: args.assertion,
        request: `${args.request.method} ${args.request.url.path.join('/')}`,
        status: error ? 'failed' : 'passed',
        error: error ? error.message : null
      };

      if (error) {
        testResults.failed.push(testInfo);
      } else {
        testResults.passed.push(testInfo);
      }
    });

    newmanRun.on('done', (error, summary) => {
      console.log('\n📊 API Test Summary:');
      console.log(`✅ Passed: ${summary.run.stats.tests.pending}`);
      console.log(`❌ Failed: ${summary.run.stats.tests.failed}`);
      console.log(`⏱️  Duration: ${summary.run.timings.completed - summary.run.timings.started}ms`);
    });
  });
}

// Performance test scenarios
async function runPerformanceTests() {
  console.log('🚀 Running performance test scenarios...\n');

  // Scenario 1: Normal load
  console.log('📈 Scenario 1: Normal Load Test');
  await runAPITests({
    iterationCount: 10,
    delayRequest: 100
  });

  // Scenario 2: High load
  console.log('\n📈 Scenario 2: High Load Test');
  await runAPITests({
    iterationCount: 50,
    delayRequest: 0
  });

  // Scenario 3: Sustained load
  console.log('\n📈 Scenario 3: Sustained Load Test');
  await runAPITests({
    iterationCount: 100,
    delayRequest: 500
  });
}

// Security test scenarios
async function runSecurityTests() {
  console.log('🔒 Running security test scenarios...\n');

  const securityCollection = {
    ...require(TEST_CONFIG.collection),
    item: require(TEST_CONFIG.collection).item.filter(
      folder => folder.name === 'Security Tests'
    )
  };

  await runAPITests({
    collection: securityCollection
  });
}

// Regression test suite
async function runRegressionTests() {
  console.log('🔄 Running regression test suite...\n');

  // Run all tests with baseline comparison
  const currentResults = await runAPITests();
  
  // Compare with baseline if exists
  const baselinePath = path.join(__dirname, 'reports', 'baseline-api-results.json');
  if (fs.existsSync(baselinePath)) {
    const baseline = JSON.parse(fs.readFileSync(baselinePath, 'utf8'));
    
    console.log('\n📊 Regression Analysis:');
    console.log(`Performance change: ${
      ((currentResults.performance.avgResponseTime - baseline.performance.avgResponseTime) / 
       baseline.performance.avgResponseTime * 100).toFixed(2)
    }%`);
    
    // Check for regressions
    if (currentResults.performance.avgResponseTime > baseline.performance.avgResponseTime * 1.1) {
      console.warn('⚠️  Performance regression detected!');
    }
  }
}

// Main execution
if (require.main === module) {
  const mode = process.argv[2] || 'all';

  (async () => {
    try {
      switch (mode) {
        case 'performance':
          await runPerformanceTests();
          break;
        case 'security':
          await runSecurityTests();
          break;
        case 'regression':
          await runRegressionTests();
          break;
        case 'all':
        default:
          await runAPITests();
          await runPerformanceTests();
          await runSecurityTests();
      }
      process.exit(0);
    } catch (error) {
      console.error('❌ Test execution failed:', error);
      process.exit(1);
    }
  })();
}

module.exports = {
  runAPITests,
  runPerformanceTests,
  runSecurityTests,
  runRegressionTests
};