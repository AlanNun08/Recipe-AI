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
      <h2>Login to BuildYourSmartCart</h2>
      
      {error && (
        <div style={{ 
          color: 'red', 
          marginBottom: '15px',
          backgroundColor: '#ffe6e6',
          padding: '10px',
          borderRadius: '5px',
          border: '1px solid #ffb3b3'
        }}>
          {error}
        </div>
      )}
      
      <form onSubmit={handleLogin}>
        <div style={{ marginBottom: '15px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '5px', 
            fontWeight: 'bold',
            fontSize: '14px'
          }}>
            Email Address
          </label>
          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ 
              width: '100%', 
              padding: '12px', 
              fontSize: '16px',
              border: '2px solid #ddd',
              borderRadius: '5px',
              outline: 'none'
            }}
            onFocus={(e) => e.target.style.borderColor = '#007bff'}
            onBlur={(e) => e.target.style.borderColor = '#ddd'}
          />
        </div>
        
        <div style={{ marginBottom: '20px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '5px', 
            fontWeight: 'bold',
            fontSize: '14px'
          }}>
            Password
          </label>
          <input
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ 
              width: '100%', 
              padding: '12px', 
              fontSize: '16px',
              border: '2px solid #ddd',
              borderRadius: '5px',
              outline: 'none'
            }}
            onFocus={(e) => e.target.style.borderColor = '#007bff'}
            onBlur={(e) => e.target.style.borderColor = '#ddd'}
          />
        </div>
        
        <button 
          type="submit" 
          disabled={loading}
          style={{ 
            width: '100%', 
            padding: '12px', 
            fontSize: '16px',
            fontWeight: 'bold',
            backgroundColor: loading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      
      <div style={{ 
        marginTop: '20px', 
        textAlign: 'center',
        fontSize: '14px',
        color: '#666'
      }}>
        <p>
          Don't have an account? <a href="/register" style={{ color: '#007bff' }}>Sign up</a>
        </p>
        <p>
          <a href="/forgot-password" style={{ color: '#007bff' }}>Forgot your password?</a>
        </p>
      </div>
    </div>
  );
};

export default LoginComponent;
