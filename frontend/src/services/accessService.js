import api from './api';
import { toast } from 'react-toastify';

const accessService = {
  /**
   * Fetch all access rules for all roles
   */
  fetchAllAccess: async () => {
    try {
      const response = await api.get('/access/');
      return response.data;
    } catch (error) {
      console.error('Error fetching access rules:', error);
      toast.error('Failed to fetch access rules');
      return null;
    }
  },

  /**
   * Fetch access rules for a specific role
   * @param {number} roleId - The role ID to fetch access rules for
   */
  fetchAccessByRole: async (roleId) => {
    try {
      const response = await api.get(`/access/${roleId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching access rules for role ID ${roleId}:`, error);
      toast.error(`Failed to fetch access rules for role ID ${roleId}`);
      return null;
    }
  },

  /**
   * Update access rules for a specific role
   * @param {object} accessData - The access data to be updated
   */
  updateAccess: async (accessData) => {
    try {
      const response = await api.post('/access/', accessData);
      toast.success('Access updated successfully');
      return response.data;
    } catch (error) {
      console.error('Error updating access rules:', error);
      toast.error('Failed to update access rules');
      return null;
    }
  },

  /**
   * Delete access rules for a specific role
   * @param {number} roleId - The role ID to delete access rules for
   */
  deleteAccess: async (roleId) => {
    try {
      await api.delete('/access/', { data: { role_id: roleId } });
      toast.success('Access deleted successfully');
    } catch (error) {
      console.error(`Error deleting access rules for role ID ${roleId}:`, error);
      toast.error('Failed to delete access rules');
    }
  }
};

export default accessService;
