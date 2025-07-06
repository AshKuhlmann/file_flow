import React, { useState, useEffect, useCallback } from 'react';

export default function App() {
    const [files, setFiles] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [targetDirectory, setTargetDirectory] = useState(null);

    const fetchTriageFiles = useCallback(async (dirPath) => {
        if (!dirPath) return;
        setIsLoading(true);
        setError(null);
        const result = await window.electronAPI.getTriageList(dirPath);
        if (result.success) {
            setFiles(result.files);
        } else {
            setError(result.error);
        }
        setIsLoading(false);
    }, []);

    useEffect(() => {
        fetchTriageFiles(targetDirectory);
    }, [targetDirectory, fetchTriageFiles]);

    const handleSetDirectory = async () => {
        const path = await window.electronAPI.openDirectoryDialog();
        if (path) {
            setTargetDirectory(path);
        }
    };

    const handleFileAction = async (filePath, action, options = {}) => {
        const result = await window.electronAPI.performFileAction({
            path: filePath,
            action,
            ...options
        });
        if (result.success) {
            fetchTriageFiles(targetDirectory);
        } else {
            setError(result.error);
        }
    };

    if (!targetDirectory) {
        return (
            <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
                <div className="text-center">
                    <h1 className="text-2xl font-bold mb-4">Welcome to the File Sorter</h1>
                    <p className="mb-6">Please select a directory to start organizing.</p>
                    <button
                        onClick={handleSetDirectory}
                        className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 px-6 rounded-lg"
                    >
                        Select Folder
                    </button>
                    {error && <p className="text-red-500 mt-4">{error}</p>}
                </div>
            </div>
        );
    }

    return (
        <div className="bg-gray-900 text-white min-h-screen font-sans flex antialiased">
            <main className="flex-1 p-8">
                <h1 className="text-2xl font-bold">Files in: {targetDirectory}</h1>
                <button onClick={() => setTargetDirectory(null)} className="text-sm text-indigo-400 mb-4">Change Folder</button>
                {isLoading && <p>Loading files...</p>}
                {error && <p className="text-red-500">{error}</p>}
                <p>Your main UI goes here. You have {files.length} files to triage.</p>
            </main>
        </div>
    );
}
