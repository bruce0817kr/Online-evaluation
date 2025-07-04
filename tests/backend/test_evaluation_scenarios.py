
import pytest
import requests
import os

# Configuration - IMPORTANT: Update these with your actual backend URL and credentials
BASE_URL = "http://localhost:8080" # Your backend API base URL
ADMIN_USER = {"username": "admin", "password": "admin_password"} # Replace with actual admin credentials
SECRETARY_USER = {"username": "secretary", "password": "secretary_password"} # Replace with actual secretary credentials
EVALUATOR_USER = {"username": "evaluator", "password": "evaluator_password"} # Replace with actual evaluator credentials

# --- Helper Functions for Authentication ---
def get_token(username, password):
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"username": username, "password": password})
    response.raise_for_status()
    return response.json()["access_token"]

@pytest.fixture(scope="module")
def admin_token():
    return get_token(ADMIN_USER["username"], ADMIN_USER["password"])

@pytest.fixture(scope="module")
def secretary_token():
    return get_token(SECRETARY_USER["username"], SECRETARY_USER["password"])

@pytest.fixture(scope="module")
def evaluator_token():
    return get_token(EVALUATOR_USER["username"], EVALUATOR_USER["password"])

# --- Test Scenarios ---

# Scenario 1: Evaluation Creation and Setup (Admin/Secretary)
def test_evaluation_creation_and_setup(secretary_token):
    headers = {"Authorization": f"Bearer {secretary_token}"}

    # 1. Create a new evaluation project
    project_data = {
        "name": "Test Evaluation Project",
        "description": "Project for testing evaluation scenarios",
        "start_date": "2025-07-01T00:00:00Z",
        "end_date": "2025-07-31T23:59:59Z"
    }
    response = requests.post(f"{BASE_URL}/api/v1/projects/", json=project_data, headers=headers)
    assert response.status_code == 201, f"Failed to create project: {response.text}"
    project_id = response.json()["id"]
    print(f"Created project with ID: {project_id}")

    # 2. Create evaluation criteria/template (assuming an endpoint for this)
    # This part is highly dependent on your actual API for evaluation templates/criteria
    # For demonstration, let's assume a simple endpoint to add criteria to a project
    criteria_data = {
        "project_id": project_id,
        "name": "Technical Competency",
        "max_score": 100,
        "weight": 0.5
    }
    # Replace with your actual endpoint for creating/assigning criteria
    response = requests.post(f"{BASE_URL}/api/v1/evaluation_criteria/", json=criteria_data, headers=headers)
    assert response.status_code == 201, f"Failed to create criteria: {response.text}"
    criteria_id = response.json()["id"]
    print(f"Created criteria with ID: {criteria_id}")

    # 3. Assign evaluators to the project (assuming an endpoint for this)
    # This part assumes you have evaluator user IDs available
    # For this test, we'll use a placeholder evaluator ID. In a real scenario, you'd fetch existing evaluator IDs.
    evaluator_user_id = "some_evaluator_user_id" # Replace with an actual evaluator user ID from your DB
    assignment_data = {
        "project_id": project_id,
        "evaluator_id": evaluator_user_id
    }
    # Replace with your actual endpoint for assigning evaluators
    response = requests.post(f"{BASE_URL}/api/v1/project_assignments/", json=assignment_data, headers=headers)
    assert response.status_code == 201, f"Failed to assign evaluator: {response.text}"
    print(f"Assigned evaluator {evaluator_user_id} to project {project_id}")

    # Clean up (optional, but good practice for tests)
    # You might need admin privileges for deletion
    # requests.delete(f"{BASE_URL}/api/v1/projects/{project_id}", headers=headers)


# Scenario 2: Evaluation Participation and Submission (Evaluator)
def test_evaluation_participation_and_submission(evaluator_token):
    headers = {"Authorization": f"Bearer {evaluator_token}"}

    # Pre-requisite: A project and evaluation assigned to the evaluator
    # In a real test, you'd set up this pre-requisite or use a known project/assignment
    # For simplicity, let's assume a project_id and assignment_id are known or created by a setup fixture
    project_id = "existing_project_id_for_evaluator" # Replace with an actual project ID assigned to the evaluator
    evaluation_id = "existing_evaluation_id_for_evaluator" # Replace with an actual evaluation ID

    # 1. Evaluator views assigned evaluations
    response = requests.get(f"{BASE_URL}/api/v1/evaluations/assigned", headers=headers)
    assert response.status_code == 200, f"Failed to get assigned evaluations: {response.text}"
    assigned_evaluations = response.json()
    assert any(e["id"] == evaluation_id for e in assigned_evaluations), "Assigned evaluation not found"
    print(f"Evaluator viewed assigned evaluations: {assigned_evaluations}")

    # 2. Evaluator submits scores/feedback for an evaluation
    submission_data = {
        "evaluation_id": evaluation_id,
        "criteria_scores": [
            {"criteria_id": "criteria_id_1", "score": 85, "feedback": "Good technical understanding"},
            {"criteria_id": "criteria_id_2", "score": 90, "feedback": "Excellent presentation skills"}
        ],
        "overall_feedback": "Overall a strong candidate."
    }
    # Replace with your actual endpoint for submitting evaluation
    response = requests.post(f"{BASE_URL}/api/v1/evaluations/submit", json=submission_data, headers=headers)
    assert response.status_code == 200, f"Failed to submit evaluation: {response.text}"
    print(f"Evaluator submitted evaluation for {evaluation_id}")

    # 3. Verify submission (optional, but good practice)
    # You might need an endpoint to view a specific submitted evaluation
    response = requests.get(f"{BASE_URL}/api/v1/evaluations/{evaluation_id}/submission", headers=headers)
    assert response.status_code == 200, f"Failed to retrieve submitted evaluation: {response.text}"
    submitted_evaluation = response.json()
    assert submitted_evaluation["overall_feedback"] == "Overall a strong candidate."
    print(f"Verified submission for {evaluation_id}")


# Scenario 3: Evaluation Result Viewing and Extraction (Admin/Secretary)
def test_evaluation_result_viewing_and_extraction(secretary_token):
    headers = {"Authorization": f"Bearer {secretary_token}"}

    # Pre-requisite: A completed evaluation project
    # In a real test, you'd set up this pre-requisite or use a known completed project
    completed_project_id = "completed_project_id" # Replace with an actual completed project ID

    # 1. Secretary views overall results for a project
    response = requests.get(f"{BASE_URL}/api/v1/projects/{completed_project_id}/results", headers=headers)
    assert response.status_code == 200, f"Failed to get project results: {response.text}"
    project_results = response.json()
    assert len(project_results) > 0, "No results found for the completed project"
    print(f"Secretary viewed results for project {completed_project_id}: {project_results}")

    # 2. Secretary extracts results (e.g., as a PDF or CSV)
    # This part is highly dependent on your actual API for report generation/extraction
    # For demonstration, let's assume an endpoint that returns a file
    # Replace with your actual endpoint for extracting results
    response = requests.get(f"{BASE_URL}/api/v1/projects/{completed_project_id}/export_results", headers=headers)
    # Assuming it returns a file, check content type or status
    assert response.status_code == 200, f"Failed to export results: {response.text}"
    # Example: Check if it's a PDF
    # assert response.headers["Content-Type"] == "application/pdf"
    print(f"Secretary extracted results for project {completed_project_id}")

    # Optional: Save the extracted file
    # with open(f"project_{completed_project_id}_results.pdf", "wb") as f:
    #     f.write(response.content)
    # print(f"Saved extracted results to project_{completed_project_id}_results.pdf")
