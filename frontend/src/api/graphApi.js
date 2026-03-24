import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const fetchGraph = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/graph`);
        return response.data;
    } catch (error) {
        console.error("Error fetching graph:", error);
        throw error;
    }
};

export const fetchGraphSummary = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/graph/summary`);
        return response.data;
    } catch (error) {
        console.error("Error fetching graph summary:", error);
        throw error;
    }
};

export const fetchBusinessFlowGraph = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/graph/business-flow`);
        return response.data;
    } catch (error) {
        console.error("Error fetching business flow graph:", error);
        throw error;
    }
};

export const fetchNodeNeighbors = async (nodeId) => {
    try {
        const response = await axios.get(`${API_BASE_URL}/node/${nodeId}/neighbors`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching neighbors for ${nodeId}:`, error);
        throw error;
    }
};

export const fetchExpandNode = async (nodeId, limit = 20) => {
    try {
        const response = await axios.get(`${API_BASE_URL}/graph/expand/${nodeId}`, { params: { limit } });
        return response.data;
    } catch (error) {
        console.error(`Error expanding node ${nodeId}:`, error);
        throw error;
    }
};

export const fetchNodeDetails = async (nodeId) => {
    try {
        const response = await axios.get(`${API_BASE_URL}/node/${nodeId}`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching node details for ${nodeId}:`, error);
        throw error;
    }
};

export const traceBusinessFlow = async (docId) => {
    try {
        const response = await axios.get(`${API_BASE_URL}/trace/${docId}`);
        return response.data;
    } catch (error) {
        console.error(`Error tracing flow for ${docId}:`, error);
        throw error;
    }
};

export const runChatQuery = async (question, options = {}) => {
    try {
        const payload = {
            question,
            use_llm: options.useLlm ?? true,
            top_k: options.topK ?? 15
        };
        const response = await axios.post(`${API_BASE_URL}/chat/query`, payload);
        return response.data;
    } catch (error) {
        console.error("Error running chat query:", error);
        throw error;
    }
};
