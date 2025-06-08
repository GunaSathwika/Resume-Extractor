import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import ResumeUploader from './components/ResumeUploader';
import ResumeList from './components/ResumeList';
import Header from './components/Header';
import Footer from './components/Footer';
import { ThemeProvider } from './contexts/ThemeContext';
import './App.css';
import './tailwind.css';

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <Router>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Header />
        <div className="flex flex-col">
          <div className="flex-1">
            <main className="py-8">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center mb-8">
                  <h1 className="text-2xl font-bold text-gray-900">
                    <Link to="/" className="text-blue-600 hover:text-blue-800">Resume Manager</Link>
                  </h1>
                  <nav>
                    <Link 
                      to="/upload" 
                      className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Upload Resume
                    </Link>
                  </nav>
                </div>
                <Routes>
                  <Route path="/" element={<Navigate to="/resumes" replace />} />
                  <Route path="/upload" element={
                    <div className="w-full">
                      <ResumeUploader 
                        onUploadSuccess={(id) => {
                          console.log('Resume uploaded successfully with ID:', id);
                        }} 
                      />
                    </div>
                  } />
                  <Route path="/resumes" element={<ResumeList />} />
                </Routes>
              </div>
            </main>
          </div>
          <Footer />
        </div>
      </div>
    </Router>
  </ThemeProvider>
  );
};

export default App;
