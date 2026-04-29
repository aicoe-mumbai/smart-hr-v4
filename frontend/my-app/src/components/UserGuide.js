import React from 'react';
import { jsPDF } from 'jspdf';

const generatePDF = () => {
  try {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 20;
    const maxWidth = pageWidth - 2 * margin;
    let yPos = margin;

  const addNewPageIfNeeded = (requiredSpace = 10) => {
    if (yPos + requiredSpace > pageHeight - margin) {
      doc.addPage();
      yPos = margin;
      return true;
    }
    return false;
  };

  const addTitle = (text) => {
    addNewPageIfNeeded(20);
    doc.setFontSize(22);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 51, 102);
    doc.text(text, pageWidth / 2, yPos, { align: 'center' });
    yPos += 15;
  };

  const addSectionHeader = (text) => {
    addNewPageIfNeeded(15);
    doc.setFontSize(16);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 102, 204);
    doc.text(text, margin, yPos);
    yPos += 10;
  };

  const addSubHeader = (text) => {
    addNewPageIfNeeded(12);
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(51, 51, 51);
    doc.text(text, margin, yPos);
    yPos += 8;
  };

  const addText = (text, indent = 0) => {
    if (!text) return;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(51, 51, 51);
    const lines = doc.splitTextToSize(text, maxWidth - indent);
    lines.forEach(line => {
      addNewPageIfNeeded(7);
      doc.text(line, margin + indent, yPos);
      yPos += 6;
    });
  };

  const addBullet = (text) => {
    if (!text) return;
    addNewPageIfNeeded(7);
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(51, 51, 51);
    doc.text('\u2022', margin + 5, yPos);
    const lines = doc.splitTextToSize(text, maxWidth - 15);
    lines.forEach((line, idx) => {
      if (idx > 0) addNewPageIfNeeded(7);
      doc.text(line, margin + 12, yPos);
      yPos += 6;
    });
  };

  const addSpace = (space = 5) => {
    yPos += space;
  };

  // Cover Page
  doc.setFillColor(0, 51, 102);
  doc.rect(0, 0, pageWidth, pageHeight, 'F');
  doc.setFontSize(32);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(255, 255, 255);
  doc.text('Goal Assist', pageWidth / 2, pageHeight / 2 - 20, { align: 'center' });
  doc.setFontSize(24);
  doc.text('User Guide', pageWidth / 2, pageHeight / 2 + 10, { align: 'center' });
  doc.setFontSize(12);
  doc.setFont('helvetica', 'normal');
  doc.text('Version 2.0', pageWidth / 2, pageHeight - 30, { align: 'center' });

  // New page for content
  doc.addPage();
  yPos = margin;

  addTitle('Introduction');
  addText('Goal Assist is a comprehensive tool designed to help you create SMART goals, validate them against established criteria, and analyze coverage against company Thrust Areas (TA) and Group Objectives (GO). This guide will help you understand how to use all features effectively.');
  addSpace(10);

  addSectionHeader('PART 1: CREATING AND VALIDATING GOALS');
  addSpace(5);

  addSubHeader('Creating a New Goal');
  addText('Step 1: Fill in the Form');
  addBullet('Enter your goal in the "Goal" field');
  addBullet('Complete all required fields including Measure of Success, KPI metrics, etc.');
  addBullet('Select your Business Unit (BU) from the dropdown');
  addBullet('Select appropriate Thrust Area and Group Objective');
  addBullet('Optionally select Crosslinked BUs if your goal spans multiple business units');
  addBullet('Set start and end dates');
  addSpace(5);
  doc.setFont('helvetica', 'italic');
  addText('Tip: Be as specific as possible in your goal description to get the best analysis.');
  doc.setFont('helvetica', 'normal');
  addSpace(5);

  addText('Step 2: Analyze the Goal');
  addBullet('Click the "Analyze Goal" button to submit your goal for validation');
  addBullet('The system will evaluate your goal against SMART criteria, calculate alignment with BU objectives, provide AI-powered recommendations, and show alignment percentages');
  addBullet('Review the feedback carefully, including SMARTness percentage, goal alignment scores, BU Alignment Analysis table, and specific recommendations');
  addSpace(5);

  addText('Step 3: Refine Your Goal');
  addBullet('Based on the feedback, make necessary adjustments to your goal');
  addBullet('Re-analyze as needed until you are satisfied with the results');
  addBullet('When done, check "Have you reviewed all the details above and confirmed this as your final goal?"');
  addSpace(5);

  addText('Step 4: Submit All Goals Checkpoint');
  addBullet('After confirming your final goal, you\'ll see: "Have you submitted all goals for the upcoming year?"');
  addBullet('Check this box ONLY when you have submitted ALL your goals for the year');
  addBullet('Once checked, you will be automatically redirected to the Gap Analysis page');
  addSpace(10);

  addSectionHeader('PART 2: GAP ANALYSIS');
  addSpace(5);

  addSubHeader('What is Gap Analysis?');
  addText('Gap Analysis helps you identify coverage gaps in your goal portfolio by comparing your goals against all company Thrust Areas and Group Objectives. This ensures comprehensive alignment with organizational priorities.');
  addSpace(5);

  addSubHeader('Running Gap Analysis');
  addText('Step 1: Access Gap Analysis');
  addBullet('After submitting all goals, you will be redirected to the Gap Analysis page');
  addBullet('Or click "Run Gap Analysis" button from the Previous Validations page');
  addBullet('Or navigate directly to the Gap Analysis page');
  addSpace(5);

  addText('Step 2: Select Goals to Analyze');
  addBullet('You will see all your submitted goals listed');
  addBullet('Select individual goals by clicking on them or their checkboxes');
  addBullet('Use "Select All" button to quickly select all goals');
  addBullet('Click "Analyze X Selected Goals" button to start analysis');
  addSpace(5);

  addText('Step 3: Review Analysis Results');
  addBullet('Overall Assessment: Summary of your goal portfolio');
  addBullet('Strengths: Areas where you have good coverage');
  addBullet('Critical Gaps: Thrust Areas or Group Objectives you have not addressed');
  addBullet('Strategic Recommendations: Prioritized suggestions (High/Medium/Low priority)');
  addBullet('Balance Analysis: Assessment of goal distribution');
  addBullet('Risk Assessment: Potential risks from coverage gaps');
  addSpace(5);

  addText('Step 4: Save and Return');
  addBullet('Your gap analysis is automatically saved to your history');
  addBullet('A success message confirms the save');
  addBullet('Click "Return to Home" button to go back to the main page');
  addSpace(5);

  addSubHeader('Viewing Gap Analysis History');
  addBullet('Navigate to "Previous Validations" page');
  addBullet('Click on "Gap Analysis History" tab');
  addBullet('View all your past gap analyses with analysis date, number of goals, coverage percentages, and AI insights');
  addBullet('Click "View Full Analysis" to expand and see complete details');
  addBullet('Click "+ New Analysis" to run a new gap analysis');
  addSpace(5);

  addText('Coverage Indicators:');
  doc.setTextColor(0, 128, 0);
  addBullet('Green (75% or more): Excellent coverage');
  doc.setTextColor(204, 153, 0);
  addBullet('Yellow (50-74%): Moderate coverage, some gaps exist');
  doc.setTextColor(204, 0, 0);
  addBullet('Red (less than 50%): Poor coverage, significant gaps');
  doc.setTextColor(51, 51, 51);
  addSpace(10);

  addSectionHeader('PART 3: MANAGING YOUR GOALS');
  addSpace(5);

  addSubHeader('Using the Goals Section');
  addText('The "Form" and "Goals" sections allow you to switch between input and output views. To ensure your data is not lost:');
  addBullet('Complete the form before switching sections');
  addBullet('Use the "Save Goal as Text" feature to keep a copy of your work');
  addBullet('Remember that validation data is preserved in the "Previous Validations" section');
  addSpace(5);

  addSubHeader('Previous Validations - My Goals Tab');
  addText('In the "My Goals" tab, you can:');
  addBullet('View all your previously validated goals in a table format');
  addBullet('See which goals are marked as final or not');
  addBullet('Edit existing goals by clicking the "Edit" button');
  addBullet('Delete goals you no longer need');
  addBullet('Copy a goal name using the "Copy Goal" button');
  addBullet('Save complete goal details using the "Save Goal as Text" button');
  addBullet('Export all goals to Excel using the export button');
  addBullet('Navigate between pages if you have many goals');
  addSpace(5);

  addSubHeader('Previous Validations - Gap Analysis History Tab');
  addText('In the "Gap Analysis History" tab, you can:');
  addBullet('View all your past gap analyses as cards');
  addBullet('See coverage percentages with visual progress bars');
  addBullet('Read AI-generated insights and recommendations');
  addBullet('Expand any analysis to view full details');
  addBullet('Run a new gap analysis using the "+ New Analysis" button');
  addSpace(10);

  addSectionHeader('PART 4: UNDERSTANDING KEY FEATURES');
  addSpace(5);

  addSubHeader('Business Unit (BU) Alignment');
  addBullet('Your goal is matched against objectives from your BU and crosslinked BUs');
  addBullet('The system shows alignment percentage for each BU');
  addBullet('Higher alignment means your goal is well-connected to BU objectives');
  addBullet('Review the BU Alignment Analysis table in the validation results');
  addSpace(5);

  addSubHeader('Thrust Areas (TA) and Group Objectives (GO)');
  addBullet('Thrust Areas represent strategic focus areas for the organization');
  addBullet('Group Objectives are specific organizational goals');
  addBullet('Your goals should align with relevant TAs and GOs');
  addBullet('Gap Analysis identifies which TAs/GOs are not covered by your goals');
  addSpace(5);

  addSubHeader('Crosslinked Business Units');
  addBullet('Select crosslinked BUs if your goal impacts multiple business units');
  addBullet('The system will check alignment with objectives from all selected BUs');
  addBullet('This ensures comprehensive coverage across organizational boundaries');
  addSpace(5);

  addSubHeader('AI-Powered Insights');
  addBullet('The system uses Azure OpenAI to provide intelligent analysis');
  addBullet('AI evaluates SMART criteria, alignment, and strategic fit');
  addBullet('Recommendations are prioritized (High/Medium/Low) based on importance');
  addBullet('Strategic insights help you understand portfolio balance and risks');
  addSpace(10);

  addSectionHeader('PART 5: BEST PRACTICES');
  addSpace(5);

  addSubHeader('Tips for Creating Effective SMART Goals');
  addBullet('Specific: Clearly define what you want to accomplish');
  addBullet('Measurable: Include quantifiable metrics to track progress');
  addBullet('Achievable: Ensure the goal is realistic given available resources');
  addBullet('Relevant: Align with organizational objectives and priorities');
  addBullet('Time-bound: Set clear start and end dates');
  addSpace(5);

  addSubHeader('Goal Portfolio Best Practices');
  addBullet('Diversify Coverage: Ensure your goals cover multiple Thrust Areas and Group Objectives');
  addBullet('Balance Priorities: Mix strategic, operational, and developmental goals');
  addBullet('Consider Dependencies: Use crosslinked BUs for goals that require collaboration');
  addBullet('Regular Review: Run gap analysis periodically to identify coverage gaps');
  addBullet('Address Critical Gaps: Prioritize creating goals for uncovered TAs/GOs');
  addBullet('Aim for 75%+ Coverage: Target at least 75% coverage for both TA and GO');
  addSpace(5);

  addSubHeader('Gap Analysis Workflow');
  addBullet('Submit all your goals for the year');
  addBullet('Run comprehensive gap analysis on all goals');
  addBullet('Review AI insights and identify critical gaps');
  addBullet('Create additional goals to address high-priority gaps');
  addBullet('Re-run gap analysis to verify improved coverage');
  addBullet('Save final analysis for future reference');
  addSpace(10);

  addSectionHeader('PART 6: TROUBLESHOOTING');
  addSpace(5);

  addSubHeader('Common Issues and Solutions');
  addText('Q: My goal shows low alignment percentage');
  addText('A: Review the BU Alignment Analysis table and adjust your goal to better match BU objectives', 5);
  addSpace(3);
  addText('Q: Gap analysis shows many critical gaps');
  addText('A: This is normal if you have few goals. Create additional goals targeting uncovered TAs/GOs', 5);
  addSpace(3);
  addText('Q: I cannot find my gap analysis');
  addText('A: Go to Previous Validations page and click "Gap Analysis History" tab', 5);
  addSpace(3);
  addText('Q: The system says gap analysis is required');
  addText('A: You have confirmed goals but have not run gap analysis. Click "Run Gap Analysis" button', 5);
  addSpace(3);
  addText('Q: I want to update a goal after gap analysis');
  addText('A: Edit the goal from "My Goals" tab, then run a new gap analysis to see updated coverage', 5);
  addSpace(10);

  addSectionHeader('CONCLUSION');
  addSpace(5);
  addText('Goal Assist provides a comprehensive platform for creating, validating, and analyzing your goals. By following this guide and using all features effectively, you can ensure your goals are SMART, well-aligned with organizational objectives, and provide comprehensive coverage across all strategic areas.');
  addSpace(5);
  addText('For additional support, contact your system administrator or HR team.');

    doc.save('Goal-Assist-User-Guide.pdf');
  } catch (error) {
    console.error('Error generating PDF:', error);
    alert('Failed to generate PDF. Please try again or contact support.');
  }
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