import api from './api';

const authService = {
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.get('/auth/logout')
};

export default authService;
