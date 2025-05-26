'use client';

export default function Loading() {
  return (
    <div className="flex items-center justify-center h-full min-h-[50vh]">
      <div className="flex space-x-2">
        <div className="h-4 w-4 bg-primary-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
        <div className="h-4 w-4 bg-primary-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
        <div className="h-4 w-4 bg-primary-500 rounded-full animate-bounce"></div>
      </div>
    </div>
  );
}
