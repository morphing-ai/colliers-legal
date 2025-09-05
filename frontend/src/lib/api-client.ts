// Simple API client for FINRA compliance app
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://dmp.dev.morphing.ai/api';

class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const headers: any = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Request failed with status ${response.status}`);
    }

    return response.json();
  }

  // FINRA Rules endpoints
  async getRules() {
    return this.request('/compliance/rules/catalog');
  }

  async loadRules() {
    return this.request('/compliance/rules/load', { method: 'POST' });
  }

  async searchRules(query: string) {
    return this.request(`/compliance/rules/search?q=${encodeURIComponent(query)}`);
  }

  // Compliance Analysis endpoints
  async analyzeDocument(documentText: string, documentDate?: string) {
    return this.request('/compliance/analyze', {
      method: 'POST',
      body: JSON.stringify({ 
        document_text: documentText,
        document_date: documentDate 
      }),
    });
  }

  async getAnalysisResult(analysisId: string) {
    return this.request(`/compliance/analyze/${analysisId}`);
  }

  // Health check
  async healthCheck() {
    return this.request('/health');
  }
}

export const api = new ApiClient();