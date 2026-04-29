import React from 'react';
import { saveAs } from 'file-saver';

// Function to download the PDF file from assets
const downloadUserGuide = () => {
  // Path to the PDF file in assets
  const pdfUrl = process.env.PUBLIC_URL + '../assets/Goal Setting AI Console Guide.pdf';
  
  // Fetch the PDF file
  fetch(pdfUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.blob();
    })
    .then(blob => {
      // Use file-saver to save the PDF
      saveAs(blob, 'Goal Setting AI Console Guide.pdf');
    })
    .catch(error => {
      console.error('Error downloading the PDF:', error);
      alert('Failed to download the user guide. Please try again later.');
    });
};

const UserGuideButton = () => (
  <button
    onClick={downloadUserGuide}
    className="download-guide-btn"
  >
    Download User Guide
  </button>
);

export { UserGuideButton }; 