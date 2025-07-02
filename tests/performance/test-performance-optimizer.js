const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const os = require('os');
const fs = require('fs');
const path = require('path');

/**
 * High-performance test execution optimizer
 * Implements parallel test execution, smart caching, and resource optimization
 */

class TestPerformanceOptimizer {
  constructor(options = {}) {
    this.options = {
      maxWorkers: options.maxWorkers || Math.min(os.cpus().length, 8),
      cacheTTL: options.cacheTTL || 3600000, // 1 hour
      memoryLimit: options.memoryLimit || 512 * 1024 * 1024, // 512MB per worker
      timeoutPerTest: options.timeoutPerTest || 30000,
      retryAttempts: options.retryAttempts || 3,
      ...options
    };
    
    this.cache = new Map();
    this.workers = [];
    this.testQueue = [];
    this.results = [];
    this.metrics = {
      totalTests: 0,
      completedTests: 0,
      failedTests: 0,
      totalTime: 0,
      cacheHits: 0,
      cacheMisses: 0
    };
  }

  /**
   * Intelligent test partitioning based on complexity and historical data
   */
  partitionTests(testSuites) {
    const partitions = [];
    const weights = this.calculateTestWeights(testSuites);
    const targetPartitionSize = Math.ceil(testSuites.length / this.options.maxWorkers);
    
    let currentPartition = [];
    let currentWeight = 0;
    const maxWeight = weights.reduce((sum, w) => sum + w, 0) / this.options.maxWorkers;
    
    for (let i = 0; i < testSuites.length; i++) {
      const testSuite = testSuites[i];
      const weight = weights[i];
      
      if (currentPartition.length >= targetPartitionSize || 
          (currentWeight + weight > maxWeight && currentPartition.length > 0)) {
        partitions.push(currentPartition);
        currentPartition = [testSuite];
        currentWeight = weight;
      } else {
        currentPartition.push(testSuite);
        currentWeight += weight;
      }
    }
    
    if (currentPartition.length > 0) {
      partitions.push(currentPartition);
    }
    
    return partitions;
  }

  /**
   * Calculate test weights based on file size, complexity, and historical execution time
   */
  calculateTestWeights(testSuites) {
    return testSuites.map(suite => {
      const filePath = suite.path || suite;
      const cacheKey = `weight:${filePath}`;
      
      if (this.cache.has(cacheKey)) {
        this.metrics.cacheHits++;
        return this.cache.get(cacheKey).value;
      }
      
      this.metrics.cacheMisses++;
      
      let weight = 1; // Base weight
      
      try {
        const stats = fs.statSync(filePath);
        const sizeWeight = Math.log(stats.size / 1024) || 1; // Log scale based on file size
        
        const content = fs.readFileSync(filePath, 'utf8');
        const complexityWeight = this.calculateComplexity(content);
        const historicalWeight = this.getHistoricalWeight(filePath);
        
        weight = sizeWeight * complexityWeight * historicalWeight;
      } catch (error) {
        console.warn(`Warning: Could not calculate weight for ${filePath}:`, error.message);
      }
      
      this.cache.set(cacheKey, {
        value: weight,
        timestamp: Date.now()
      });
      
      return weight;
    });
  }

  /**
   * Calculate test complexity based on code patterns
   */
  calculateComplexity(content) {
    let complexity = 1;
    
    // Count test patterns
    const testMatches = content.match(/\b(test|it|describe|beforeEach|afterEach)\s*\(/g) || [];
    complexity += Math.log(testMatches.length + 1);
    
    // Count async patterns
    const asyncMatches = content.match(/\b(async|await|Promise|setTimeout|setInterval)\b/g) || [];
    complexity += asyncMatches.length * 0.5;
    
    // Count DOM operations
    const domMatches = content.match(/\b(render|fireEvent|screen|waitFor|getBy|findBy|queryBy)\b/g) || [];
    complexity += domMatches.length * 0.3;
    
    // Count API mocks
    const mockMatches = content.match(/\b(mock|jest\.fn|fetch\.mock|spy)\b/g) || [];
    complexity += mockMatches.length * 0.2;
    
    return Math.max(complexity, 1);
  }

  /**
   * Get historical execution time weight
   */
  getHistoricalWeight(filePath) {
    const historyPath = path.join(__dirname, 'test-history.json');
    
    try {
      if (fs.existsSync(historyPath)) {
        const history = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
        const fileHistory = history[filePath];
        
        if (fileHistory && fileHistory.avgExecutionTime) {
          return Math.log(fileHistory.avgExecutionTime / 1000 + 1);
        }
      }
    } catch (error) {
      console.warn('Could not read test history:', error.message);
    }
    
    return 1;
  }

  /**
   * Execute tests with optimal parallelization
   */
  async executeTests(testSuites, options = {}) {
    const startTime = Date.now();
    console.log(`🚀 Starting optimized test execution with ${this.options.maxWorkers} workers...`);
    
    this.cleanCache();
    const partitions = this.partitionTests(testSuites);
    
    console.log(`📊 Partitioned ${testSuites.length} tests into ${partitions.length} groups`);
    
    const workerPromises = partitions.map((partition, index) => 
      this.executePartition(partition, index, options)
    );
    
    const results = await Promise.all(workerPromises);
    const endTime = Date.now();
    
    this.metrics.totalTime = endTime - startTime;
    this.updateTestHistory(testSuites, results);
    
    return this.aggregateResults(results);
  }

  /**
   * Execute a partition of tests in a worker thread
   */
  async executePartition(partition, workerId, options) {
    return new Promise((resolve, reject) => {
      const worker = new Worker(__filename, {
        workerData: {
          partition,
          workerId,
          options: { ...this.options, ...options }
        }
      });
      
      let timeoutHandle = setTimeout(() => {
        worker.terminate();
        reject(new Error(`Worker ${workerId} timed out`));
      }, this.options.timeoutPerTest * partition.length * 2);
      
      worker.on('message', (result) => {
        clearTimeout(timeoutHandle);
        resolve(result);
      });
      
      worker.on('error', (error) => {
        clearTimeout(timeoutHandle);
        reject(error);
      });
      
      worker.on('exit', (code) => {
        clearTimeout(timeoutHandle);
        if (code !== 0) {
          reject(new Error(`Worker ${workerId} exited with code ${code}`));
        }
      });
    });
  }

  /**
   * Clean expired cache entries
   */
  cleanCache() {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > this.options.cacheTTL) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Update test execution history for future optimization
   */
  updateTestHistory(testSuites, results) {
    const historyPath = path.join(__dirname, 'test-history.json');
    let history = {};
    
    try {
      if (fs.existsSync(historyPath)) {
        history = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
      }
    } catch (error) {
      console.warn('Could not read existing test history:', error.message);
    }
    
    results.flat().forEach((result, index) => {
      if (testSuites[index]) {
        const filePath = testSuites[index].path || testSuites[index];
        
        if (!history[filePath]) {
          history[filePath] = {
            executions: [],
            avgExecutionTime: 0,
            successRate: 100
          };
        }
        
        const fileHistory = history[filePath];
        fileHistory.executions.push({
          timestamp: Date.now(),
          executionTime: result.executionTime || 0,
          success: result.success || false
        });
        
        // Keep only last 10 executions
        if (fileHistory.executions.length > 10) {
          fileHistory.executions = fileHistory.executions.slice(-10);
        }
        
        // Update averages
        const executions = fileHistory.executions;
        fileHistory.avgExecutionTime = executions.reduce((sum, exec) => sum + exec.executionTime, 0) / executions.length;
        fileHistory.successRate = (executions.filter(exec => exec.success).length / executions.length) * 100;
      }
    });
    
    try {
      fs.writeFileSync(historyPath, JSON.stringify(history, null, 2));
    } catch (error) {
      console.warn('Could not save test history:', error.message);
    }
  }

  /**
   * Aggregate results from all workers
   */
  aggregateResults(workerResults) {
    const aggregated = {
      success: true,
      totalTests: 0,
      passedTests: 0,
      failedTests: 0,
      totalTime: this.metrics.totalTime,
      details: [],
      performance: {
        cacheHitRate: this.metrics.cacheHits / (this.metrics.cacheHits + this.metrics.cacheMisses) * 100,
        avgTestTime: 0,
        parallelEfficiency: 0
      }
    };
    
    workerResults.flat().forEach(result => {
      if (result) {
        aggregated.totalTests += result.totalTests || 0;
        aggregated.passedTests += result.passedTests || 0;
        aggregated.failedTests += result.failedTests || 0;
        aggregated.details.push(result);
        
        if (result.failedTests > 0) {
          aggregated.success = false;
        }
      }
    });
    
    if (aggregated.totalTests > 0) {
      aggregated.performance.avgTestTime = aggregated.totalTime / aggregated.totalTests;
      aggregated.performance.parallelEfficiency = 
        (aggregated.totalTests * 1000 / aggregated.totalTime) / this.options.maxWorkers * 100;
    }
    
    return aggregated;
  }

  /**
   * Generate performance report
   */
  generatePerformanceReport(results) {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalTests: results.totalTests,
        passedTests: results.passedTests,
        failedTests: results.failedTests,
        successRate: (results.passedTests / results.totalTests * 100).toFixed(2) + '%',
        totalExecutionTime: results.totalTime + 'ms',
        averageTestTime: results.performance.avgTestTime.toFixed(2) + 'ms',
        parallelEfficiency: results.performance.parallelEfficiency.toFixed(2) + '%',
        cacheHitRate: results.performance.cacheHitRate.toFixed(2) + '%'
      },
      recommendations: this.generateRecommendations(results)
    };
    
    const reportPath = path.join(__dirname, 'reports', `performance-report-${Date.now()}.json`);
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    
    return report;
  }

  /**
   * Generate optimization recommendations
   */
  generateRecommendations(results) {
    const recommendations = [];
    
    if (results.performance.parallelEfficiency < 70) {
      recommendations.push({
        type: 'performance',
        priority: 'high',
        message: 'Consider reducing worker count or optimizing test isolation'
      });
    }
    
    if (results.performance.cacheHitRate < 50) {
      recommendations.push({
        type: 'caching',
        priority: 'medium',
        message: 'Improve test caching strategy for better performance'
      });
    }
    
    if (results.performance.avgTestTime > 5000) {
      recommendations.push({
        type: 'optimization',
        priority: 'high',
        message: 'Some tests are taking too long, consider optimizing or splitting them'
      });
    }
    
    return recommendations;
  }
}

// Worker thread execution
if (!isMainThread) {
  const { partition, workerId, options } = workerData;
  
  (async () => {
    try {
      const results = [];
      
      for (const test of partition) {
        const startTime = Date.now();
        
        try {
          // Execute individual test (this would be replaced with actual test runner)
          const result = await executeIndividualTest(test, options);
          const executionTime = Date.now() - startTime;
          
          results.push({
            test: test,
            success: true,
            totalTests: 1,
            passedTests: 1,
            failedTests: 0,
            executionTime
          });
        } catch (error) {
          const executionTime = Date.now() - startTime;
          
          results.push({
            test: test,
            success: false,
            totalTests: 1,
            passedTests: 0,
            failedTests: 1,
            executionTime,
            error: error.message
          });
        }
      }
      
      parentPort.postMessage(results);
    } catch (error) {
      parentPort.postMessage({ error: error.message });
    }
  })();
}

async function executeIndividualTest(test, options) {
  // This is a placeholder - in reality this would execute the actual test
  // using Jest, Playwright, or other test runners
  return new Promise((resolve) => {
    setTimeout(resolve, Math.random() * 1000); // Simulate test execution
  });
}

module.exports = TestPerformanceOptimizer;