import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { Message } from '../types/api';
import { sendQuery } from '../services/api';

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize session ID
  useEffect(() => {
    // Check if we have a session ID in local storage
    const storedSessionId = localStorage.getItem('sessionId');
    if (storedSessionId) {
      setSessionId(storedSessionId);
    } else {
      // Generate a new session ID
      const newSessionId = uuidv4();
      setSessionId(newSessionId);
      localStorage.setItem('sessionId', newSessionId);
    }

    // Add welcome message
    setMessages([
      {
        id: uuidv4(),
        type: 'bot',
        content: "# Welcome to the Multi-Agent AI Tutoring System!\n\nI'm here to help you with math and physics questions. Ask me anything about:\n\n- Mathematics (algebra, calculus, geometry, etc.)\n- Physics (mechanics, thermodynamics, electromagnetism, etc.)\n\nHow can I assist you today?",
        timestamp: new Date(),
      },
    ]);
  }, []);

  // Handle sending a message
  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    // Add user message to chat
    const userMessageId = uuidv4();
    const userMessage: Message = {
      id: userMessageId,
      type: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // Add typing indicator
    const typingIndicatorId = uuidv4();
    setMessages((prev) => [
      ...prev,
      {
        id: typingIndicatorId,
        type: 'bot',
        content: '<div class="typing-indicator"><span></span><span></span><span></span></div>',
        timestamp: new Date(),
      },
    ]);

    try {
      // Send query to API
      const response = await sendQuery({
        question: content,
        session_id: sessionId,
      });

      // Remove typing indicator
      setMessages((prev) => prev.filter((msg) => msg.id !== typingIndicatorId));

      // Add bot response to chat
      const botMessage: Message = {
        id: uuidv4(),
        type: 'bot',
        content: response.answer,
        timestamp: new Date(),
        agentDetails: response.agent_details,
      };

      setMessages((prev) => [...prev, botMessage]);

      // Update session ID if it changed
      if (response.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id);
        localStorage.setItem('sessionId', response.session_id);
      }
    } catch (error) {
      // Remove typing indicator
      setMessages((prev) => prev.filter((msg) => msg.id !== typingIndicatorId));

      // Add error message to chat
      const errorMessage: Message = {
        id: uuidv4(),
        type: 'bot',
        content: error instanceof Error ? error.message : 'An unexpected error occurred. Please try again.',
        timestamp: new Date(),
        isError: true,
        errorDetails: {
          code: 'ERROR',
          message: error instanceof Error ? error.message : 'Unknown error',
          retry: true,
        },
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <header className="bg-white border-b border-gray-200 p-4">
        <h1 className="text-xl font-bold text-center text-gray-800">Multi-Agent AI Tutoring System</h1>
      </header>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-3xl mx-auto">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="max-w-3xl mx-auto w-full">
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
};

export default ChatInterface;
