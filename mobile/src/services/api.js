import axios from 'axios';
import * as SecureStore from 'expo-secure-store';
import { API_BASE_URL } from '../config';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth APIs
export const authApi = {
  register: async (data) => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },
  
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },
};

// Packages API
export const packagesApi = {
  getAll: async () => {
    const response = await api.get('/packages');
    return response.data;
  },
};

// Inspections API
export const inspectionsApi = {
  create: async (buyerId, data) => {
    const response = await api.post(`/inspections?buyer_id=${buyerId}`, data);
    return response.data;
  },
  
  getBuyerInspections: async (buyerId) => {
    const response = await api.get(`/inspections/buyer/${buyerId}`);
    return response.data;
  },
  
  getAvailable: async (lat, lng, radius = 50) => {
    const response = await api.get(`/inspections/available?inspector_lat=${lat}&inspector_lng=${lng}&radius=${radius}`);
    return response.data;
  },
  
  accept: async (inspectionId, inspectorId) => {
    const response = await api.post(`/inspections/${inspectionId}/accept?inspector_id=${inspectorId}`);
    return response.data;
  },
  
  verifyCode: async (inspectionId, code, inspectorId) => {
    const response = await api.post(`/inspections/${inspectionId}/verify-code?code=${code}&inspector_id=${inspectorId}`);
    return response.data;
  },
  
  getProgress: async (inspectionId) => {
    const response = await api.get(`/inspections/${inspectionId}/progress`);
    return response.data;
  },
  
  uploadPhoto: async (inspectionId, stepName, photoUri) => {
    const formData = new FormData();
    formData.append('step_name', stepName);
    formData.append('file', {
      uri: photoUri,
      type: 'image/jpeg',
      name: `${stepName}_${Date.now()}.jpg`,
    });
    
    const response = await api.post(`/inspections/${inspectionId}/upload-photo`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  
  completeStep: async (inspectionId, stepName, notes = '') => {
    const response = await api.post(`/inspections/${inspectionId}/complete-step?step_name=${stepName}&notes=${encodeURIComponent(notes)}`);
    return response.data;
  },
  
  submitReport: async (inspectionId, inspectorId, data) => {
    const response = await api.post(`/inspections/${inspectionId}/submit-report?inspector_id=${inspectorId}`, data);
    return response.data;
  },
};

// Reports API
export const reportsApi = {
  getByInspection: async (inspectionId) => {
    const response = await api.get(`/reports/inspection/${inspectionId}`);
    return response.data;
  },
};

// Inspector API
export const inspectorApi = {
  getProfile: async (userId) => {
    const response = await api.get(`/inspector/profile/${userId}`);
    return response.data;
  },
  
  updateProfile: async (userId, lat, lng, radius = 50) => {
    const response = await api.put(`/inspector/profile/${userId}?location_lat=${lat}&location_lng=${lng}&radius_miles=${radius}`);
    return response.data;
  },
  
  verifyId: async (userId) => {
    const response = await api.post(`/inspector/verify-id/${userId}`);
    return response.data;
  },
  
  getJobs: async (inspectorId) => {
    const response = await api.get(`/inspector/jobs/${inspectorId}`);
    return response.data;
  },
};

// Notifications API
export const notificationsApi = {
  get: async (userId) => {
    const response = await api.get(`/notifications/${userId}`);
    return response.data;
  },
  
  markRead: async (notificationId) => {
    const response = await api.post(`/notifications/${notificationId}/read`);
    return response.data;
  },
};

// Storage helpers
export const storage = {
  setUser: async (user) => {
    await SecureStore.setItemAsync('user', JSON.stringify(user));
  },
  
  getUser: async () => {
    const user = await SecureStore.getItemAsync('user');
    return user ? JSON.parse(user) : null;
  },
  
  removeUser: async () => {
    await SecureStore.deleteItemAsync('user');
  },
  
  setLanguage: async (lang) => {
    await SecureStore.setItemAsync('language', lang);
  },
  
  getLanguage: async () => {
    return await SecureStore.getItemAsync('language');
  },
};

export default api;
