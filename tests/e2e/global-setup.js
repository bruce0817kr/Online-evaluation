/**
 * Global setup for Playwright tests
 * Initializes test environment and prepares test data
 */
const { chromium } = require('@playwright/test');

async function globalSetup() {
  console.log('🚀 Starting global setup for Online Evaluation System tests...');
  
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Wait for backend to be ready
    console.log('⏳ Waiting for backend service...');
    await waitForService('http://localhost:8080/api/health', 60000);
    
    // Wait for frontend to be ready
    console.log('⏳ Waiting for frontend service...');
    await waitForService('http://localhost:3001', 60000);
    
    // Initialize system if needed
    console.log('🔧 Initializing system...');
    await initializeSystem(page);
    
    // Setup test data
    console.log('📊 Setting up test data...');
    await setupTestData(page);
    
    console.log('✅ Global setup completed successfully');
    
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

/**
 * Wait for service to be available
 */
async function waitForService(url, timeout = 60000) {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return true;
      }
    } catch (error) {
      // Service not ready yet
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  throw new Error(`Service at ${url} not available after ${timeout}ms`);
}

/**
 * Initialize system
 */
async function initializeSystem(page) {
  try {
    const response = await page.request.post('http://localhost:8080/api/init');
    if (response.ok()) {
      console.log('✅ System initialized');
    } else {
      console.log('ℹ️ System already initialized or init not needed');
    }
  } catch (error) {
    console.warn('⚠️ System initialization warning:', error.message);
  }
}

/**
 * Setup test data
 */
async function setupTestData(page) {
  try {
    // Login as admin
    const loginResponse = await page.request.post('http://localhost:8080/api/auth/login', {
      data: {
        login_id: 'admin',
        password: 'admin123'
      }
    });
    
    if (!loginResponse.ok()) {
      throw new Error('Failed to login as admin for test data setup');
    }
    
    const loginData = await loginResponse.json();
    const token = loginData.access_token;
    
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
    
    // Create test project if not exists
    const projectsResponse = await page.request.get('http://localhost:8080/api/projects', {
      headers
    });
    
    let testProject = null;
    if (projectsResponse.ok()) {
      const projects = await projectsResponse.json();
      testProject = projects.find(p => p.name === 'E2E Test Project');
    }
    
    if (!testProject) {
      const createProjectResponse = await page.request.post('http://localhost:8080/api/projects', {
        data: {
          name: 'E2E Test Project',
          description: 'Project for E2E testing'
        },
        headers
      });
      
      if (createProjectResponse.ok()) {
        testProject = await createProjectResponse.json();
        console.log('✅ Created test project');
      }
    }
    
    // Create test company if not exists
    if (testProject) {
      const companiesResponse = await page.request.get(`http://localhost:8080/api/companies?project_id=${testProject.id}`, {
        headers
      });
      
      let testCompany = null;
      if (companiesResponse.ok()) {
        const companies = await companiesResponse.json();
        testCompany = companies.find(c => c.name === 'E2E Test Company');
      }
      
      if (!testCompany) {
        const createCompanyResponse = await page.request.post('http://localhost:8080/api/companies', {
          data: {
            name: 'E2E Test Company',
            business_number: '123-45-67890',
            project_id: testProject.id
          },
          headers
        });
        
        if (createCompanyResponse.ok()) {
          testCompany = await createCompanyResponse.json();
          console.log('✅ Created test company');
        }
      }
    }
    
    // Create test evaluator if not exists
    const evaluatorsResponse = await page.request.get('http://localhost:8080/api/evaluators', {
      headers
    });
    
    let testEvaluator = null;
    if (evaluatorsResponse.ok()) {
      const evaluators = await evaluatorsResponse.json();
      testEvaluator = evaluators.find(e => e.email === 'test.evaluator@test.com');
    }
    
    if (!testEvaluator) {
      const createEvaluatorResponse = await page.request.post('http://localhost:8080/api/evaluators', {
        data: {
          name: 'Test Evaluator',
          phone: '010-1234-5678',
          email: 'test.evaluator@test.com'
        },
        headers
      });
      
      if (createEvaluatorResponse.ok()) {
        testEvaluator = await createEvaluatorResponse.json();
        console.log('✅ Created test evaluator');
      }
    }
    
    // Store test data for use in tests
    const testData = {
      project: testProject,
      company: testCompany,
      evaluator: testEvaluator
    };
    
    // Save to file for tests to access
    const fs = require('fs');
    const path = require('path');
    
    const testDataDir = path.join(__dirname, '../test-data');
    if (!fs.existsSync(testDataDir)) {
      fs.mkdirSync(testDataDir, { recursive: true });
    }
    
    fs.writeFileSync(
      path.join(testDataDir, 'setup-data.json'),
      JSON.stringify(testData, null, 2)
    );
    
    console.log('✅ Test data setup completed');
    
  } catch (error) {
    console.warn('⚠️ Test data setup warning:', error.message);
  }
}

module.exports = globalSetup;
