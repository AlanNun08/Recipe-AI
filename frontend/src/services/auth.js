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

  // Login user with verification handling
  async login(credentials) {
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });
      
      const data = await response.json();
      
      // Handle verification required (403 status)
      if (response.status === 403 && data.status === 'verification_required') {
        // Store user data temporarily for verification process
        localStorage.setItem('pendingVerification', JSON.stringify({
          user_id: data.user_id,
          email: data.email
        }));
        
        // Return the verification required response
        return {
          status: 'verification_required',
          message: data.message,
          user_id: data.user_id,
          email: data.email,
          action: 'verify_account'
        };
      }
      
      // Handle other errors
      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Successful login
      if (data.status === 'success') {
        // Store user data
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // Clear any pending verification data
        localStorage.removeItem('pendingVerification');
        
        return data;
      }
      
      throw new Error('Unexpected login response');
      
    } catch (error) {
      console.error('Auth service login error:', error);
      throw error;
    }
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
  },

  // Get pending verification data
  getPendingVerification() {
    const pending = localStorage.getItem('pendingVerification');
    return pending ? JSON.parse(pending) : null;
  },

  // Clear pending verification data
  clearPendingVerification() {
    localStorage.removeItem('pendingVerification');
  },

  // Verify email with code and complete login
  async verifyEmailAndLogin(userId, code) {
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
      const error = await response.json();
      throw new Error(error.detail || 'Verification failed');
    }
    
    const data = await response.json();
    
    // After successful verification, get the user data
    // You might want to add an endpoint to get user data after verification
    // For now, we'll clear pending verification
    this.clearPendingVerification();
    
    return data;
  }
};
