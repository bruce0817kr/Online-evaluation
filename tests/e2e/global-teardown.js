/**
 * Global teardown for Playwright tests
 * Cleanup test environment and test data
 */
async function globalTeardown() {
  console.log('🧹 Starting global teardown for Online Evaluation System tests...');
  
  try {
    // Cleanup test data if needed
    await cleanupTestData();
    
    // Generate test report summary
    await generateTestSummary();
    
    console.log('✅ Global teardown completed successfully');
    
  } catch (error) {
    console.error('❌ Global teardown failed:', error);
  }
}

/**
 * Cleanup test data
 */
async function cleanupTestData() {
  try {
    const fs = require('fs');
    const path = require('path');
    
    // Clean up temporary test files
    const testDataDir = path.join(__dirname, '../test-data');
    if (fs.existsSync(testDataDir)) {
      const files = fs.readdirSync(testDataDir);
      files.forEach(file => {
        if (file.startsWith('temp-') || file.includes('test-upload')) {
          fs.unlinkSync(path.join(testDataDir, file));
        }
      });
    }
    
    console.log('✅ Test data cleanup completed');
    
  } catch (error) {
    console.warn('⚠️ Test data cleanup warning:', error.message);
  }
}

/**
 * Generate test summary
 */
async function generateTestSummary() {
  try {
    const fs = require('fs');
    const path = require('path');
    
    const resultsDir = path.join(__dirname, '../../test-results');
    const resultsFile = path.join(resultsDir, 'results.json');
    
    if (fs.existsSync(resultsFile)) {
      const results = JSON.parse(fs.readFileSync(resultsFile, 'utf8'));
      
      const summary = {
        timestamp: new Date().toISOString(),
        totalTests: results.stats?.total || 0,
        passed: results.stats?.passed || 0,
        failed: results.stats?.failed || 0,
        skipped: results.stats?.skipped || 0,
        duration: results.stats?.duration || 0,
        success: (results.stats?.failed || 0) === 0
      };
      
      // Write summary
      fs.writeFileSync(
        path.join(resultsDir, 'summary.json'),
        JSON.stringify(summary, null, 2)
      );
      
      // Print summary to console
      console.log('\n📊 Test Execution Summary:');
      console.log(`   Total Tests: ${summary.totalTests}`);
      console.log(`   ✅ Passed: ${summary.passed}`);
      console.log(`   ❌ Failed: ${summary.failed}`);
      console.log(`   ⏭️ Skipped: ${summary.skipped}`);
      console.log(`   ⏱️ Duration: ${Math.round(summary.duration / 1000)}s`);
      console.log(`   🎯 Success: ${summary.success ? 'YES' : 'NO'}`);
      
    }
    
  } catch (error) {
    console.warn('⚠️ Test summary generation warning:', error.message);
  }
}

module.exports = globalTeardown;
