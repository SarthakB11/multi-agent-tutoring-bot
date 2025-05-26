'use client';

import { Suspense } from 'react';
import dynamic from 'next/dynamic';
import Loading from '@/components/Loading';

// Dynamically import the ChatInterface component to ensure it only runs on the client
const ChatInterface = dynamic(() => import('@/components/ChatInterface'), {
  loading: () => <Loading />,
  ssr: false,
});

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col">
      <header className="bg-white border-b border-gray-200 p-4">
        <h1 className="text-xl font-bold text-center text-gray-800">Multi-Agent AI Tutoring System</h1>
      </header>
      
      <Suspense fallback={<Loading />}>
        <ChatInterface />
      </Suspense>
    </main>
  );
}
