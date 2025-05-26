'use client';

import { QueryRequest, QueryResponse } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Send a query to the backend API
 * @param params Query parameters
 * @returns Promise with the query response
 */
export async function sendQuery(params: {
  question: string;
  user_id?: string;
  session_id?: string;
}): Promise<QueryResponse> {
  try {
    const request: QueryRequest = {
      query: params.question,
      user_id: params.user_id || 'anonymous',
      session_id: params.session_id,
      debug: process.env.NODE_ENV === 'development',
    };

    const response = await fetch(`${API_URL}/api/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error?.message || 'Failed to get response from the server');
    }

    return await response.json();
  } catch (error) {
    console.error('API error:', error);
    throw error;
  }
}

/**
 * Check if the API server is available
 * @returns Promise with boolean indicating if the server is available
 */
export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return response.ok;
  } catch (error) {
    console.error('Health check error:', error);
    return false;
  }
}
