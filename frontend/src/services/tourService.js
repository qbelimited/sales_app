import api from './api';

class TourService {
  static async getTourStatus(userId) {
    try {
      const { data } = await api.get(`/help/tours/list?userId=${userId}`);
      return data.help_tours?.[0] || null; // Return first tour or null if none exist
    } catch (error) {
      if (error.response?.status === 404) {
        return null; // No tour exists yet
      }
      throw error;
    }
  }

  static async getTourProgress(userId) {
    try {
      const { data } = await api.get(`/help/tours/progress`);
      return data;
    } catch (error) {
      throw error;
    }
  }

  static async getTourSteps(tourId) {
    try {
      const { data } = await api.get(`/help/tours/${tourId}/steps`);
      return data;
    } catch (error) {
      throw error;
    }
  }

  static async getStepStatus(tourId, stepId) {
    try {
      const { data } = await api.get(`/help/tours/${tourId}/steps/${stepId}/status`);
      return data;
    } catch (error) {
      throw error;
    }
  }

  static async markStepCompleted(tourId, stepId) {
    try {
      await api.put(`/help/tours/${tourId}/steps/${stepId}/status`, { completed: true });
      return true;
    } catch (error) {
      throw error;
    }
  }

  static async markStepSkipped(tourId, stepId) {
    try {
      await api.put(`/help/tours/${tourId}/steps/${stepId}/status`, { skipped: true });
      return true;
    } catch (error) {
      throw error;
    }
  }

  static async resetTour(tourId) {
    try {
      await api.post(`/help/tours/${tourId}/reset`);
      return true;
    } catch (error) {
      throw error;
    }
  }

  static async createTour(tourData) {
    try {
      const { data } = await api.post('/help/tours', tourData);
      return data;
    } catch (error) {
      throw error;
    }
  }

  static async updateTour(tourId, tourData) {
    try {
      const { data } = await api.put(`/help/tours/${tourId}`, tourData);
      return data;
    } catch (error) {
      throw error;
    }
  }

  static async deleteTour(tourId) {
    try {
      await api.delete(`/help/tours/${tourId}`);
      return true;
    } catch (error) {
      throw error;
    }
  }
}

export default TourService;
