
import { test, expect } from '@playwright/test';

// Configuration - IMPORTANT: Update these with your actual frontend URL and credentials
const BASE_URL = 'http://localhost:3001'; // Your frontend application base URL
const ADMIN_USERNAME = 'admin'; // Replace with actual admin username
const ADMIN_PASSWORD = 'admin_password'; // Replace with actual admin password
const SECRETARY_USERNAME = 'secretary'; // Replace with actual secretary username
const SECRETARY_PASSWORD = 'secretary_password'; // Replace with actual secretary password
const EVALUATOR_USERNAME = 'evaluator'; // Replace with actual evaluator username
const EVALUATOR_PASSWORD = 'evaluator_password'; // Replace with actual evaluator password

// Helper function for login
async function login(page, username, password) {
    await page.goto(`${BASE_URL}/login`); // Adjust login path if different
    await page.fill('input[name="username"]', username); // Adjust selector if different
    await page.fill('input[name="password"]', password); // Adjust selector if different
    await page.click('button[type="submit"]'); // Adjust selector if different
    await expect(page).toHaveURL(`${BASE_URL}/dashboard`); // Adjust dashboard path if different
}

// --- Test Scenarios ---

test.describe('Evaluation Scenarios - Frontend UI', () => {

    test('Scenario 1: Evaluation Creation and Setup (Secretary)', async ({ page }) => {
        // Login as Secretary
        await login(page, SECRETARY_USERNAME, SECRETARY_PASSWORD);

        // 1. Navigate to Project Creation Page
        await page.click('text=Projects'); // Adjust selector for navigation to projects list
        await page.click('text=Create New Project'); // Adjust selector for create project button
        await expect(page).toHaveURL(`${BASE_URL}/projects/new`); // Adjust path

        // 2. Fill Project Details and Create
        const projectName = `Test UI Project ${Date.now()}`;
        await page.fill('input[name="projectName"]', projectName); // Adjust selector
        await page.fill('textarea[name="projectDescription"]', 'UI test project description'); // Adjust selector
        await page.fill('input[name="startDate"]', '2025-07-01'); // Adjust selector and date format
        await page.fill('input[name="endDate"]', '2025-07-31'); // Adjust selector and date format
        await page.click('button[type="submit"]'); // Adjust selector for project creation submit

        // Verify project creation (e.g., redirected to project list or detail page)
        await expect(page).toHaveURL(/.*\/projects\/.*/); // Adjust to match your project detail/list URL pattern
        await expect(page.locator(`text=${projectName}`)).toBeVisible();

        // 3. Navigate to Evaluation Criteria Setup (assuming it's part of project detail or a separate section)
        // This part is highly dependent on your actual UI flow
        // For demonstration, let's assume there's a button/link on the project detail page
        await page.click(`text=${projectName}`); // Click on the newly created project
        await page.click('text=Manage Criteria'); // Adjust selector for managing criteria
        await expect(page).toHaveURL(/.*\/projects\/.+\/criteria/); // Adjust path

        // 4. Add Evaluation Criteria
        await page.fill('input[name="criteriaName"]', 'Technical Skills'); // Adjust selector
        await page.fill('input[name="maxScore"]', '100'); // Adjust selector
        await page.fill('input[name="weight"]', '0.6'); // Adjust selector
        await page.click('button:has-text("Add Criteria")'); // Adjust selector
        await expect(page.locator('text=Technical Skills')).toBeVisible();

        // 5. Assign Evaluators (assuming a section for this)
        await page.click('text=Assign Evaluators'); // Adjust selector
        // Select an evaluator from a dropdown or list. This requires knowing an evaluator's name/ID in the UI.
        // For example, if there's a select element:
        // await page.selectOption('select[name="evaluatorSelect"]', { label: 'Evaluator One' });
        // Or if it's a search and select:
        await page.fill('input[placeholder="Search Evaluator"]', 'Evaluator Name'); // Replace with actual evaluator name
        await page.click('text=Evaluator Name'); // Click on the found evaluator
        await page.click('button:has-text("Assign")'); // Adjust selector
        await expect(page.locator('text=Evaluator Name assigned')).toBeVisible(); // Adjust verification

        // Logout
        await page.click('text=Logout'); // Adjust selector
        await expect(page).toHaveURL(`${BASE_URL}/login`);
    });

    test('Scenario 2: Evaluation Participation and Submission (Evaluator)', async ({ page }) => {
        // Login as Evaluator
        await login(page, EVALUATOR_USERNAME, EVALUATOR_PASSWORD);

        // 1. Navigate to Assigned Evaluations
        await page.click('text=My Evaluations'); // Adjust selector for navigation
        await expect(page).toHaveURL(`${BASE_URL}/evaluations/assigned`); // Adjust path

        // 2. Select an Evaluation to Participate
        // This assumes there's an evaluation assigned to this evaluator
        const evaluationToSelect = 'Test UI Project'; // Part of the project name or evaluation title
        await page.click(`text=${evaluationToSelect}`); // Click on the evaluation link/card
        await expect(page).toHaveURL(/.*\/evaluations\/.+\/participate/); // Adjust path

        // 3. Fill out Evaluation Form
        // This depends heavily on your form structure
        await page.fill('input[name="criteria1Score"]', '90'); // Adjust selector for score input
        await page.fill('textarea[name="criteria1Feedback"]', 'Very good understanding.'); // Adjust selector for feedback
        await page.fill('input[name="criteria2Score"]', '80');
        await page.fill('textarea[name="criteria2Feedback"]', 'Needs minor improvement in communication.');
        await page.fill('textarea[name="overallFeedback"]', 'Overall a solid performance.'); // Adjust selector

        // 4. Submit Evaluation
        await page.click('button:has-text("Submit Evaluation")'); // Adjust selector

        // Verify submission success (e.g., success message, redirection)
        await expect(page.locator('text=Evaluation submitted successfully')).toBeVisible(); // Adjust verification
        await expect(page).toHaveURL(`${BASE_URL}/evaluations/assigned`); // Redirect back to assigned list

        // Logout
        await page.click('text=Logout');
        await expect(page).toHaveURL(`${BASE_URL}/login`);
    });

    test('Scenario 3: Evaluation Result Viewing and Extraction (Secretary)', async ({ page }) => {
        // Login as Secretary
        await login(page, SECRETARY_USERNAME, SECRETARY_PASSWORD);

        // 1. Navigate to Project Results Page
        await page.click('text=Projects'); // Adjust selector
        await page.click('text=View Results'); // Adjust selector for a button/link to results
        await expect(page).toHaveURL(`${BASE_URL}/projects/results`); // Adjust path

        // 2. Select a Completed Project to View Results
        const completedProject = 'Test UI Project'; // Assuming the project from Scenario 1 is completed
        await page.click(`text=${completedProject}`); // Click on the project link/card
        await expect(page).toHaveURL(/.*\/projects\/.+\/results/); // Adjust path

        // 3. Verify Results Display
        await expect(page.locator('text=Overall Score:')).toBeVisible(); // Adjust verification
        await expect(page.locator('text=Evaluator Feedback:')).toBeVisible(); // Adjust verification

        // 4. Extract Results (e.g., Download PDF/CSV)
        // This assumes a button for export
        const [download] = await Promise.all([
            page.waitForEvent('download'),
            page.click('button:has-text("Export Results")') // Adjust selector
        ]);
        // Verify download (e.g., check filename or type)
        expect(download.suggestedFilename()).toMatch(/.*\.pdf|.*\.csv/); // Adjust expected file type
        console.log(`Downloaded file: ${download.suggestedFilename()}`);

        // Logout
        await page.click('text=Logout');
        await expect(page).toHaveURL(`${BASE_URL}/login`);
    });
});
