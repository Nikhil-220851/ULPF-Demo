import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8010',
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
    const response = await apiClient.post('/process', { raw_payload: rawPayload });
    return response.data;
  } catch (error) {
    console.error("Process log failed", error);
    throw error;
  }
};

// events: array of strings (legacy) OR objects {raw_payload, source_file, source_file_index}
export const processBatch = async (events) => {
  try {
    const response = await apiClient.post('/process/batch', { events });
    return response.data;
  } catch (error) {
    console.error("Process batch failed", error);
    throw error;
  }
};

export const confirmPlugin = async (name, signature, fieldMappings) => {
  try {
    const response = await apiClient.post('/plugins/confirm', {
      name,
      signature,
      field_mappings: fieldMappings,
    });
    return response.data;
  } catch (error) {
    console.error("Confirm plugin failed", error);
    throw error;
  }
};

export const getPlugins = async () => {
  try {
    const response = await apiClient.get('/plugins');
    return response.data;
  } catch (error) {
    console.error("Get plugins failed", error);
    throw error;
  }
};

export const deletePlugin = async (pluginId) => {
  try {
    const response = await apiClient.delete(`/plugins/${pluginId}`);
    return response.data;
  } catch (error) {
    console.error("Delete plugin failed", error);
    throw error;
  }
};

export const updatePlugin = async (pluginId, updateData) => {
  try {
    const response = await apiClient.put(`/plugins/${pluginId}`, updateData);
    return response.data;
  } catch (error) {
    console.error("Update plugin failed", error);
    throw error;
  }
};

export default apiClient;
