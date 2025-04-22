import React from 'react';
import { saveAs } from 'file-saver';

// Simplified version that doesn't use @react-pdf/renderer
// which has compatibility issues with the current environment
const generatePDF = () => {
  const pdfContent = `
Goal Assist User Guide

Introduction
Goal Assist is a tool designed to help you create SMART goals and validate them against established criteria. 
This guide will help you understand how to use the tool effectively.

Creating a New Goal
Step 1: Fill in the Form
- Enter your goal in the "Goal" field
- Complete all required fields including Measure of Success, KPI metrics, etc.
- Select appropriate options from the dropdowns
- Set start and end dates
Tip: Be as specific as possible in your goal description to get the best analysis.

Step 2: Analyze the Goal
- Click the "Analyze Goal" button to submit your goal for validation
- The system will evaluate your goal against SMART criteria and provide feedback
- Review the suggestions carefully

Step 3: Refine Your Goal
- Based on the feedback, make necessary adjustments to your goal
- Re-analyze as needed until you're satisfied with the results
- When you're done, check "Have you reviewed all the details above and confirmed this as your final goal?"

Using the Goals Section
The "Form" and "Goals" sections allow you to switch between input and output views. To ensure your data isn't lost:
- Complete the form before switching sections
- Use the "Save Goal as Text" feature to keep a copy of your work
- Remember that validation data is preserved in the "Previous Validations" section

Previous Validations
In the Previous Validations page, you can:
- View all your previously validated goals
- Edit existing goals by clicking the "Edit" button
- Delete goals you no longer need
- Copy a goal name using the "Copy Goal" button
- Save complete goal details using the "Save Goal as Text" button
- Export all goals to Excel using the export button
- Download this user guide for reference

Tips for Creating Effective SMART Goals
- Specific: Clearly define what you want to accomplish
- Measurable: Include quantifiable metrics to track progress
- Achievable: Ensure the goal is realistic given available resources
- Relevant: Align with organizational objectives and priorities
- Time-bound: Set clear start and end dates
`;

  const blob = new Blob([pdfContent], { type: 'text/plain;charset=utf-8' });
  saveAs(blob, 'goal-assist-user-guide.txt');
};

const UserGuideButton = () => (
  <button
    onClick={generatePDF}
    className="download-guide-btn"
  >
    Download User Guide
  </button>
);

export { UserGuideButton }; 