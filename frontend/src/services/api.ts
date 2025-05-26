import axios from 'axios';
import { QueryRequest, QueryResponse } from '../types/api';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const sendQuery = async (params: {
  question: string;
  session_id?: string;
  user_id?: string;
}): Promise<QueryResponse> => {
  try {
    const request: QueryRequest = {
      question: params.question,
      session_id: params.session_id,
      user_id: params.user_id || 'anonymous',
      debug: process.env.NODE_ENV === 'development',
    };

    const response = await axios.post(`${API_URL}/api/query`, request);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.error?.message || 'Failed to get response from the server');
    }
    throw error;
  }
};
