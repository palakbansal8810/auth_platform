import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate, useSearchParams } from 'react-router-dom';
import './Login.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Check for error in URL (from OAuth failures)
  useEffect(() => {
    const errorParam = searchParams.get('error');
    if (errorParam) {
      if (errorParam === 'auth_failed') {
        setError('Authentication failed. Please try again.');
      } else if (errorParam === 'no_code') {
        setError('No authorization code received.');
      } else if (errorParam === 'okta_auth_failed') {
        setError('Okta authentication failed. Please try again.');
      } else {
        setError('An error occurred during authentication.');
      }
    }
  }, [searchParams]);

  const handleLocalAuth = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const endpoint = isRegister ? '/auth/local/register' : '/auth/local/login';
      const data = isRegister ? { email, password, name } : { email, password };
      
      const response = await axios.post(`${API_URL}${endpoint}`, data);
      
      // Store the token from the JSON response
      if (response.data && response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        
        // Navigate to dashboard
        navigate('/dashboard');
      } else {
        setError('Invalid response from server');
      }
    } catch (err) {
      console.error('Auth error:', err);
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.response?.status === 401) {
        setError('Invalid email or password');
      } else if (err.response?.status === 400) {
        setError(err.response?.data?.detail || 'Invalid request');
      } else {
        setError('Authentication failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = `${API_URL}/auth/google/login`;
  };

  const handleOktaLogin = () => {
    window.location.href = `${API_URL}/auth/okta/login`;
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>🔐 Auth Platform</h1>
        <p className="subtitle">{isRegister ? 'Create your account' : 'Welcome back'}</p>
        
        {error && <div className="error">{error}</div>}
        
        <form onSubmit={handleLocalAuth}>
          {isRegister && (
            <input
              type="text"
              placeholder="Full Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required={isRegister}
              disabled={loading}
            />
          )}
          <input
            type="email"
            placeholder="Email Address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
            autoComplete="email"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
            minLength="6"
            autoComplete={isRegister ? "new-password" : "current-password"}
          />
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Please wait...' : (isRegister ? 'Create Account' : 'Sign In')}
          </button>
        </form>

        <div className="divider">OR</div>

        <button onClick={handleGoogleLogin} className="btn-google" disabled={loading}>
          <span>🔵</span> Continue with Google
        </button>
        
        <button onClick={handleOktaLogin} className="btn-okta" disabled={loading}>
          <span>🟦</span> Continue with Okta
        </button>

        <p className="toggle-auth">
          {isRegister ? 'Already have an account?' : "Don't have an account?"}
          <button 
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              setError('');
            }} 
            disabled={loading}
          >
            {isRegister ? 'Sign In' : 'Sign Up'}
          </button>
        </p>
      </div>
    </div>
  );
}

export default Login;