'use client';

import dynamic from 'next/dynamic';

// Dynamically import the dashboard page as the main page
const DashboardPage = dynamic(() => import('./dashboard/page'), { ssr: false });

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <DashboardPage />
    </div>
  );
}