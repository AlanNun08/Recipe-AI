const API_BASE = '/api';

export const authService = {
  // Register new user
  async register(userData) {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });
    
    if (!response.ok) {
      throw new Error('Registration failed');
    }
    
    const data = await response.json();
    // Store token
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    
    return data;
  },

  // Login user
  async login(credentials) {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });
    
    if (!response.ok) {
      throw new Error('Login failed');
    }
    
    const data = await response.json();
    // Store token
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    
    return data;
  },

  // Get current user
  async getMe() {
    const token = localStorage.getItem('token');
    
    const response = await fetch(`${API_BASE}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to get user');
    }
    
    return response.json();
  },

  // Logout
  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  // Get stored token
  getToken() {
    return localStorage.getItem('token');
  },

  // Check if user is logged in
  isAuthenticated() {
    return !!localStorage.getItem('token');
  },

  // Test database connection
  async testDatabase() {
    try {
      const response = await fetch(`${API_BASE}/db/test`);
      const data = await response.json();
      console.log('Database test result:', data);
      return data;
    } catch (error) {
      console.error('Database test failed:', error);
      throw error;
    }
  },

  // Check API health
  async checkHealth() {
    try {
      const response = await fetch(`${API_BASE}/health`);
      const data = await response.json();
      console.log('Health check result:', data);
      return data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  },

  // Resend verification code
  async resendCode(email) {
    const response = await fetch(`${API_BASE}/auth/resend-code`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to resend verification code');
    }
    
    return response.json();
  },

  // Verify email with code
  async verifyEmail(userId, code) {
    const response = await fetch(`${API_BASE}/auth/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        user_id: userId, 
        code: code 
      }),
    });
    
    if (!response.ok) {
      throw new Error('Verification failed');
    }
    
    return response.json();
  }
};
