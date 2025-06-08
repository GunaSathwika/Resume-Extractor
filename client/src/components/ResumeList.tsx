import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MagnifyingGlassIcon as SearchIcon, EyeIcon, TrashIcon, ArrowDownTrayIcon as DownloadIcon, TagIcon } from '@heroicons/react/24/outline';

interface Resume {
  _id: string;
  id: string;
  name: string;
  email: string;
  phone: string;
  skills: string[];
  experience: {
    role: string;
    company: string;
    duration: string;
    description: string;
  }[];
}

const ResumeList: React.FC = () => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  const fetchResumes = async () => {
    try {
      const response = await axios.get('http://localhost:8000/resumes');
      setResumes(response.data);
    } catch (error) {
      console.error('Error fetching resumes:', error);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, []);

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this resume?')) return;

    try {
      await axios.delete(`http://localhost:8000/resumes/${id}`);
      fetchResumes();
    } catch (error) {
      console.error('Error deleting resume:', error);
    }
  };

  const handleView = async (id: string) => {
    try {
      const response = await axios.get(`http://localhost:8000/resumes/${id}`);
      setSelectedResume(response.data);
    } catch (error) {
      console.error('Error fetching resume details:', error);
    }
  };

  const filteredResumes = resumes.filter((resume) => {
    const matchesSearch = resume.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      resume.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      resume.phone.toLowerCase().includes(searchTerm.toLowerCase()) ||
      resume.skills.some(skill => skill.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesTags = selectedTags.length === 0 ||
      resume.skills.some(skill => selectedTags.includes(skill));

    return matchesSearch && matchesTags;
  });

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div className="relative w-64">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <SearchIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            placeholder="Search resumes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            aria-label="Search resumes"
          />
        </div>
        
        <div className="flex gap-2">
          {['React', 'Node.js', 'Python', 'JavaScript', 'Java'].map((tag, index) => (
            <button
              key={`${tag}-${index}`}
              onClick={() => {
                if (selectedTags.includes(tag)) {
                  setSelectedTags(selectedTags.filter(t => t !== tag));
                } else {
                  setSelectedTags([...selectedTags, tag]);
                }
              }}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors duration-200 ${
                selectedTags.includes(tag)
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
              title={`Filter by ${tag}`}
            >
              <TagIcon className="w-4 h-4 inline-block mr-1" />
              {tag}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        {filteredResumes.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">
              No resumes found. Upload your first resume to get started!
            </p>
          </div>
        ) : (
          filteredResumes.map((resume, resumeIndex) => (
            <div
              key={`${resume.id}-${resumeIndex}`}
              className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300"
            >
              <div className="p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">
                      {resume.name}
                    </h3>
                    <div className="mt-2 flex flex-col gap-2">
                      <p className="text-sm text-gray-600">
                        <span className="font-medium">Email:</span> {resume.email}
                      </p>
                      <p className="text-sm text-gray-600">
                        <span className="font-medium">Phone:</span> {resume.phone}
                      </p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {resume.skills.map((skill, index) => (
                          <span
                            key={`${skill}-${index}`}
                            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleView(resume.id);
                      }}
                      className="p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200"
                      title="View details"
                    >
                      <EyeIcon className="h-5 w-5 text-gray-600" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(resume.id);
                      }}
                      className="p-2 hover:bg-red-100 rounded-lg transition-colors duration-200"
                      title="Delete resume"
                    >
                      <TrashIcon className="h-5 w-5 text-red-600" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        // Add download functionality
                      }}
                      className="p-2 hover:bg-green-100 rounded-lg transition-colors duration-200"
                      title="Download resume"
                    >
                      <DownloadIcon className="h-5 w-5 text-green-600" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {selectedResume && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center">
          <div className="bg-white rounded-lg p-6 w-96">
            <h2 className="text-xl font-semibold mb-4">Resume Details</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold">Basic Information</h3>
                <p>Name: {selectedResume.name}</p>
                <p>Email: {selectedResume.email}</p>
                <p>Phone: {selectedResume.phone}</p>
              </div>
              <div>
                <h3 className="font-semibold">Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedResume.skills.map((skill) => (
                    <span
                      key={skill}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="font-semibold">Work Experience</h3>
                {selectedResume.experience.map((exp, index) => (
                  <div key={index} className="mt-2">
                    <h4 className="font-medium">
                      {exp.company} - {exp.role}
                    </h4>
                    <p className="text-gray-600">{exp.duration}</p>
                    <p className="mt-1">{exp.description}</p>
                  </div>
                ))}
              </div>
            </div>
            <button
              onClick={() => setSelectedResume(null)}
              className="mt-4 w-full bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResumeList;
