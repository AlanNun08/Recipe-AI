// This file can be removed or simplified since we're making direct API calls
// Keeping minimal structure for future use

export const authService = {
  async login(credentials) {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Login failed');
    }

    return data;
  },

  async register(userData) {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Registration failed');
    }

    return data;
  },

  async verifyCode(email, verificationCode) {
    const response = await fetch('/api/auth/verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, verification_code: verificationCode }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Verification failed');
    }

    return data;
  },

  async resendVerificationCode(email) {
    const response = await fetch('/api/auth/resend-verification', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to resend code');
    }

    return data;
  },

  async requestPasswordReset(email) {
    const response = await fetch('/api/auth/request-password-reset', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to send reset code');
    }

    return data;
  },

  async verifyPasswordResetCode(email, verificationCode) {
    const response = await fetch('/api/auth/verify-password-reset-code', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, verification_code: verificationCode }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to verify reset code');
    }

    return data;
  },

  async resetPassword(email, verificationCode, newPassword) {
    const response = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        verification_code: verificationCode,
        new_password: newPassword,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to reset password');
    }

    return data;
  },

  getPendingVerification() {
    const stored = localStorage.getItem('pendingVerification');
    return stored ? JSON.parse(stored) : null;
  },

  setPendingVerification(data) {
    localStorage.setItem('pendingVerification', JSON.stringify(data));
  },

  clearPendingVerification() {
    localStorage.removeItem('pendingVerification');
  },

  logout() {
    localStorage.removeItem('user');
    localStorage.removeItem('userPreferences');
    localStorage.removeItem('pendingVerification');
  }
};
