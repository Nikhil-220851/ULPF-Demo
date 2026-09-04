import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const checkHealth = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    console.error("Health check failed", error);
    throw error;
  }
};

export const processLog = async (rawPayload) => {
  try {
    // Note: this must match the backend's expected structure for the /process route.
    // If process route doesn't accept payload yet, we'll still send it.
    const response = await apiClient.post('/process', { raw_payload: rawPayload });
    return response.data;
  } catch (error) {
    console.error("Process log failed", error);
    throw error;
  }
};

export default apiClient;
