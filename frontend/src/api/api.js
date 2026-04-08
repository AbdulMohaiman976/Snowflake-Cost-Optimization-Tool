import axios from 'axios';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  'https://snowflake-cost-optimization-tool-production.up.railway.app';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const connectToSnowflake = async (credentials) => {
  try {
    const response = await api.post('/session/connect', credentials, {
      timeout: 120000, // 120 seconds
    });
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw error.response?.data?.detail || error.message;
  }
};

export const loadSession = async (token) => {
  try {
    const response = await api.get(`/session/${token}`);
    return response.data;
  } catch (error) {
    throw error.response?.data?.detail || error.message;
  }
};

export const pollAIInsights = async (token) => {
  try {
    const response = await api.get(`/session/${token}/ai`);
    return response.data;
  } catch (error) {
    throw error.response?.data?.detail || error.message;
  }
};

export const generateAgentPlan = async (token, tabName) => {
  try {
    const response = await api.post(`/agent/${tabName}`, { token, mode: 'steps' });
    return response.data;
  } catch (error) {
    throw error.response?.data?.detail || error.message;
  }
};

export default api;
