import React, { createContext, useReducer, useEffect } from 'react';
import authService from '../services/authService';

const AuthContext = createContext();

const initialState = {
  isAuthenticated: false,
  user: null,
  role: null,
  loading: true,
  error: null,
};

const authReducer = (state, action) => {
  switch (action.type) {
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload.user,
        role: action.payload.role,
        loading: false,
        error: null,
      };
    case 'LOGOUT':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        role: null,
        loading: false,
      };
    case 'AUTH_ERROR':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        role: null,
        loading: false,
        error: action.payload,
      };
    case 'SET_LOADING':
      return {
        ...state,
        loading: action.payload,
      };
    default:
      return state;
  }
};

export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  useEffect(() => {
    const checkAuthStatus = async () => {
      dispatch({ type: 'SET_LOADING', payload: true });
      try {
        const savedRole = JSON.parse(localStorage.getItem('userRole'));
        const isLoggedIn = await authService.isLoggedIn();

        if (savedRole && isLoggedIn) {
          const user = authService.getUser();
          if (user) {
            dispatch({
              type: 'LOGIN_SUCCESS',
              payload: { user, role: savedRole },
            });
          } else {
            dispatch({ type: 'LOGOUT' });
            authService.logout();
          }
        } else {
          dispatch({ type: 'LOGOUT' });
          authService.logout();
        }
      } catch (error) {
        console.error('Failed to check authentication status:', error);
        dispatch({ type: 'AUTH_ERROR', payload: 'Failed to check authentication status.' });
        authService.logout();
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    checkAuthStatus();
  }, []);

  const login = async (credentials) => {
    try {
      const response = await authService.login(credentials);
      if (response?.user) {
        const userRole = response.user.role;
        localStorage.setItem('userRole', JSON.stringify(userRole));
        dispatch({
          type: 'LOGIN_SUCCESS',
          payload: { user: response.user, role: userRole },
        });
      }
    } catch (error) {
      console.error('Login failed:', error);
      dispatch({ type: 'AUTH_ERROR', payload: 'Login failed. Please try again.' });
      throw error; // Optionally rethrow to allow further handling
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
      dispatch({ type: 'LOGOUT' });
    } catch (error) {
      console.error('Logout failed:', error);
      dispatch({ type: 'AUTH_ERROR', payload: 'Logout failed. Please try again.' });
    }
  };

  return (
    <AuthContext.Provider value={{ state, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => React.useContext(AuthContext);
