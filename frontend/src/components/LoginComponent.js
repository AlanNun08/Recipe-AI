import React, { useState } from 'react';
import { authService } from '../services/auth';

const LoginComponent = ({ onVerificationRequired, onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const result = await authService.login({ email, password });
      
      console.log('Login result:', result); // Debug log
      
      if (result.status === 'verification_required') {
        // Password was correct but account needs verification
        console.log('Verification required, navigating to verification page');
        
        // Call callback to navigate to verification page
        if (onVerificationRequired) {
          onVerificationRequired(result);
        } else {
          // Default navigation
          window.location.href = '/verify';
        }
        
      } else if (result.status === 'success') {
        // Login successful
        console.log('Login successful:', result);
        
        if (onLoginSuccess) {
          onLoginSuccess(result);
        } else {
          // Default navigation
          alert('Login successful!');
          window.location.href = '/dashboard';
        }
      }
    } catch (error) {
      console.error('Login error:', error);
      setError('Login failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '0 auto', padding: '20px' }}>
      <h2>Login</h2>
      
      {error && (
        <div style={{ color: 'red', marginBottom: '10px' }}>
          {error}
        </div>
      )}
      
      <form onSubmit={handleLogin}>
        <div style={{ marginBottom: '10px' }}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ width: '100%', padding: '10px', fontSize: '16px' }}
          />
        </div>
        
        <div style={{ marginBottom: '10px' }}>
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: '100%', padding: '10px', fontSize: '16px' }}
          />
        </div>
        
        <button 
          type="submit" 
          disabled={loading}
          style={{ 
            width: '100%', 
            padding: '10px', 
            fontSize: '16px',
            backgroundColor: loading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
};

export default LoginComponent;
