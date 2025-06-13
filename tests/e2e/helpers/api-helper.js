/**
 * API Helper class for Online Evaluation System E2E tests
 * Provides common API interaction methods
 */
export class APIHelper {
  constructor(request) {
    this.request = request;
    this.baseURL = process.env.BACKEND_URL || 'http://localhost:8080';
    this.token = null;
  }

  /**
   * Set authentication token
   */
  setToken(token) {
    this.token = token;
  }

  /**
   * Get common headers with authentication
   */
  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    return headers;
  }

  /**
   * Health check
   */
  async healthCheck() {
    const response = await this.request.get(`${this.baseURL}/api/health`);
    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * System initialization
   */
  async initializeSystem() {
    const response = await this.request.post(`${this.baseURL}/api/init`);
    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * User login
   */
  async login(username, password) {
    const response = await this.request.post(`${this.baseURL}/api/auth/login`, {
      data: {
        login_id: username,
        password: password
      },
      headers: {
        'Content-Type': 'application/json'
      }
    });

    const result = {
      success: response.ok(),
      status: response.status(),
      data: null
    };

    if (response.ok()) {
      result.data = await response.json();
      if (result.data && result.data.access_token) {
        this.setToken(result.data.access_token);
      }
    }

    return result;
  }

  /**
   * Get current user info
   */
  async getCurrentUser() {
    const response = await this.request.get(`${this.baseURL}/api/auth/me`, {
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * Create project
   */
  async createProject(name, description) {
    const response = await this.request.post(`${this.baseURL}/api/projects`, {
      data: {
        name,
        description
      },
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * Get projects
   */
  async getProjects() {
    const response = await this.request.get(`${this.baseURL}/api/projects`, {
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * Create company
   */
  async createCompany(name, businessNumber, projectId) {
    const response = await this.request.post(`${this.baseURL}/api/companies`, {
      data: {
        name,
        business_number: businessNumber,
        project_id: projectId
      },
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * Get companies for a project
   */
  async getCompanies(projectId) {
    const url = projectId 
      ? `${this.baseURL}/api/companies?project_id=${projectId}`
      : `${this.baseURL}/api/companies`;
      
    const response = await this.request.get(url, {
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * Create evaluator
   */
  async createEvaluator(name, phone, email) {
    const response = await this.request.post(`${this.baseURL}/api/evaluators`, {
      data: {
        name,
        phone,
        email
      },
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * Get evaluators
   */
  async getEvaluators() {
    const response = await this.request.get(`${this.baseURL}/api/evaluators`, {
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * Create evaluation template
   */
  async createTemplate(name, description, projectId, items = null) {
    const defaultItems = items || [
      {
        name: "기술성",
        description: "기술의 혁신성 및 완성도",
        max_score: 30,
        weight: 1.0
      },
      {
        name: "시장성", 
        description: "시장 진입 가능성 및 성장 잠재력",
        max_score: 30,
        weight: 1.0
      },
      {
        name: "사업성",
        description: "사업 모델의 타당성 및 수익성",
        max_score: 40,
        weight: 1.0
      }
    ];

    const response = await this.request.post(`${this.baseURL}/api/templates?project_id=${projectId}`, {
      data: {
        name,
        description,
        items: defaultItems
      },
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * Get templates
   */
  async getTemplates(projectId = null) {
    const url = projectId 
      ? `${this.baseURL}/api/templates?project_id=${projectId}`
      : `${this.baseURL}/api/templates`;
      
    const response = await this.request.get(url, {
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * Create assignments
   */
  async createAssignments(evaluatorIds, companyIds, templateId, deadline) {
    const response = await this.request.post(`${this.baseURL}/api/assignments`, {
      data: {
        evaluator_ids: evaluatorIds,
        company_ids: companyIds,
        template_id: templateId,
        deadline: deadline
      },
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * Get evaluator dashboard
   */
  async getEvaluatorDashboard() {
    const response = await this.request.get(`${this.baseURL}/api/dashboard/evaluator`, {
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * Get admin dashboard
   */
  async getAdminDashboard() {
    const response = await this.request.get(`${this.baseURL}/api/dashboard/admin`, {
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * Get evaluation sheet
   */
  async getEvaluationSheet(sheetId) {
    const response = await this.request.get(`${this.baseURL}/api/evaluation-sheets/${sheetId}`, {
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * Save evaluation
   */
  async saveEvaluation(sheetId, scores) {
    const response = await this.request.post(`${this.baseURL}/api/evaluation-sheets/${sheetId}/save`, {
      data: { scores },
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * Submit evaluation
   */
  async submitEvaluation(sheetId, scores) {
    const response = await this.request.post(`${this.baseURL}/api/evaluation-sheets/${sheetId}/submit`, {
      data: { scores },
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }

  /**
   * Get project analytics
   */
  async getProjectAnalytics(projectId) {
    const response = await this.request.get(`${this.baseURL}/api/analytics/project/${projectId}`, {
      headers: this.getHeaders()
    });

    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }
}
