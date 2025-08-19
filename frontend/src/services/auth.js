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
  }
};
