import api from './api';

const salesService = {
  getSales: () => api.get('/sales/'),
  getSale: (id) => api.get(`/sales/${id}`),
  createSale: (saleData) => api.post('/sales/', saleData),
  updateSale: (id, saleData) => api.put(`/sales/${id}`, saleData),
  deleteSale: (id) => api.delete(`/sales/${id}`)
};

export default salesService;
