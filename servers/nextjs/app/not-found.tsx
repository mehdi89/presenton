import React from 'react';

const NotFound = () => {
    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 text-center p-6">
            <div className="max-w-lg mx-auto bg-white shadow-md rounded-lg p-8">
                <img
                    src="/404.svg"
                    alt="Page not found"
                    className="w-3/4 mx-auto mb-6"
                />
                <h1 className="text-3xl font-bold text-gray-800 mb-4">
                    Page Not Found
                </h1>
                <p className="text-lg text-gray-600 mb-4">
                    The page you are looking for is not available.
                </p>
            </div>
        </div>
    );
};

export default NotFound;