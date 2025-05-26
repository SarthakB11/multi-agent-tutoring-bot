import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Message } from '../types/api';

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  return (
    <div
      className={`flex mb-4 ${
        message.type === 'user' ? 'justify-end' : 'justify-start'
      }`}
    >
      <div
        className={`max-w-3/4 rounded-lg p-4 ${
          message.type === 'user'
            ? 'bg-blue-600 text-white'
            : message.isError
            ? 'bg-red-100 border border-red-300 text-red-800'
            : 'bg-white border border-gray-200'
        }`}
      >
        {message.content.includes('<div class="typing-indicator">') ? (
          <div
            dangerouslySetInnerHTML={{ __html: message.content }}
            className="h-6 flex items-center"
          />
        ) : (
          <div className="markdown">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}

        {message.agentDetails && (
          <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-500">
            <p>
              <span className="font-semibold">Agent:</span> {message.agentDetails.name}
            </p>
            {message.agentDetails.tools_used && message.agentDetails.tools_used.length > 0 && (
              <p>
                <span className="font-semibold">Tools used:</span>{' '}
                {message.agentDetails.tools_used.join(', ')}
              </p>
            )}
          </div>
        )}

        {message.isError && message.errorDetails && (
          <div className="mt-2 text-xs">
            <p className="font-semibold">Error: {message.errorDetails.code}</p>
            <p>{message.errorDetails.message}</p>
            {message.errorDetails.retry && (
              <p className="mt-1">Please try again or refresh the page.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
