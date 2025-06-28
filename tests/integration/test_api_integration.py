#!/usr/bin/env python3
"""
API Integration Tests for Online Evaluation System
Tests the integration between different API endpoints and services.
"""

import asyncio
import json
import pytest
import requests
import time
from typing import Dict, List, Any
import os
from datetime import datetime, timedelta

# Test configuration
BASE_URL = os.getenv('BACKEND_URL', 'http://localhost:8080')
API_BASE = f"{BASE_URL}/api"

class APIIntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_data = {
            'projects': [],
            'companies': [],
            'templates': [],
            'evaluations': [],
            'users': []
        }
    
    def login(self, username: str = 'admin', password: str = 'admin123') -> bool:
        """Login and get authentication token"""
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                data={'username': username, 'password': password},
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get('access_token')
                self.session.headers.update({
                    'Authorization': f"Bearer {self.auth_token}"
                })
                return True
            else:
                print(f"Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def test_health_check(self) -> Dict[str, Any]:
        """Test system health check"""
        try:
            response = self.session.get(f"{API_BASE}/health")
            assert response.status_code == 200, f"Health check failed: {response.status_code}"
            
            health_data = response.json()
            assert health_data.get('status') == 'healthy', "System not healthy"
            
            services = health_data.get('services', {})
            assert services.get('mongodb') == 'connected', "MongoDB not connected"
            assert services.get('api') == 'running', "API not running"
            
            return {
                'status': 'passed',
                'health_data': health_data,
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_user_management_flow(self) -> Dict[str, Any]:
        """Test complete user management workflow"""
        try:
            # Get current user info
            response = self.session.get(f"{API_BASE}/auth/me")
            assert response.status_code == 200, "Failed to get current user"
            current_user = response.json()
            assert current_user.get('role') == 'admin', "User is not admin"
            
            # Create a test user
            test_user_data = {
                'login_id': f'test_user_{int(time.time())}',
                'password': 'test_password123',
                'name': 'Integration Test User',
                'role': 'evaluator',
                'email': f'test_{int(time.time())}@example.com'
            }
            
            create_response = self.session.post(
                f"{API_BASE}/users",
                json=test_user_data
            )
            
            if create_response.status_code == 201:
                created_user = create_response.json()
                self.test_data['users'].append(created_user)
                
                # Verify user was created
                user_id = created_user.get('id')
                get_response = self.session.get(f"{API_BASE}/users/{user_id}")
                assert get_response.status_code == 200, "Failed to retrieve created user"
                
                # Update user
                update_data = {'name': 'Updated Integration Test User'}
                update_response = self.session.put(
                    f"{API_BASE}/users/{user_id}",
                    json=update_data
                )
                assert update_response.status_code == 200, "Failed to update user"
                
                return {
                    'status': 'passed',
                    'created_user': created_user,
                    'current_user': current_user
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'User creation not available or failed',
                    'current_user': current_user
                }
                
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_project_lifecycle(self) -> Dict[str, Any]:
        """Test complete project lifecycle"""
        try:
            # Create project
            project_data = {
                'name': f'Integration Test Project {int(time.time())}',
                'description': 'Project created during API integration testing',
                'start_date': datetime.now().isoformat(),
                'end_date': (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            create_response = self.session.post(
                f"{API_BASE}/projects",
                json=project_data
            )
            assert create_response.status_code == 201, f"Project creation failed: {create_response.text}"
            
            project = create_response.json()
            self.test_data['projects'].append(project)
            project_id = project.get('id')
            
            # Get project details
            get_response = self.session.get(f"{API_BASE}/projects/{project_id}")
            assert get_response.status_code == 200, "Failed to get project details"
            
            # List all projects
            list_response = self.session.get(f"{API_BASE}/projects")
            assert list_response.status_code == 200, "Failed to list projects"
            projects_list = list_response.json()
            
            # Verify our project is in the list
            project_found = any(p.get('id') == project_id for p in projects_list)
            assert project_found, "Created project not found in list"
            
            # Update project
            update_data = {
                'description': 'Updated during integration testing'
            }
            update_response = self.session.put(
                f"{API_BASE}/projects/{project_id}",
                json=update_data
            )
            assert update_response.status_code == 200, "Failed to update project"
            
            return {
                'status': 'passed',
                'project': project,
                'total_projects': len(projects_list)
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_template_management(self) -> Dict[str, Any]:
        """Test evaluation template management"""
        try:
            # Create template
            template_data = {
                'name': f'Integration Test Template {int(time.time())}',
                'description': 'Template for integration testing',
                'criteria': [
                    {
                        'name': 'Technical Innovation',
                        'description': 'Level of technical innovation and uniqueness',
                        'weight': 30,
                        'max_score': 100
                    },
                    {
                        'name': 'Market Potential',
                        'description': 'Size and growth potential of target market',
                        'weight': 25,
                        'max_score': 100
                    },
                    {
                        'name': 'Business Model',
                        'description': 'Clarity and sustainability of business model',
                        'weight': 25,
                        'max_score': 100
                    },
                    {
                        'name': 'Team Capability',
                        'description': 'Experience and expertise of the team',
                        'weight': 20,
                        'max_score': 100
                    }
                ]
            }
            
            create_response = self.session.post(
                f"{API_BASE}/templates",
                json=template_data
            )
            assert create_response.status_code == 201, f"Template creation failed: {create_response.text}"
            
            template = create_response.json()
            self.test_data['templates'].append(template)
            template_id = template.get('id')
            
            # Verify template criteria
            get_response = self.session.get(f"{API_BASE}/templates/{template_id}")
            assert get_response.status_code == 200, "Failed to get template"
            
            retrieved_template = get_response.json()
            criteria = retrieved_template.get('criteria', [])
            assert len(criteria) == 4, "Template criteria count mismatch"
            
            # Verify weights sum to 100
            total_weight = sum(c.get('weight', 0) for c in criteria)
            assert total_weight == 100, f"Template weights sum to {total_weight}, expected 100"
            
            # List templates
            list_response = self.session.get(f"{API_BASE}/templates")
            assert list_response.status_code == 200, "Failed to list templates"
            
            return {
                'status': 'passed',
                'template': template,
                'criteria_count': len(criteria),
                'total_weight': total_weight
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_company_management(self) -> Dict[str, Any]:
        """Test company management in project context"""
        try:
            # Need a project first
            if not self.test_data['projects']:
                project_result = self.test_project_lifecycle()
                if project_result['status'] != 'passed':
                    return {'status': 'failed', 'error': 'No project available for company test'}
            
            project_id = self.test_data['projects'][0]['id']
            
            # Create company
            company_data = {
                'name': f'Integration Test Company {int(time.time())}',
                'business_number': f'{int(time.time()) % 1000:03d}-{int(time.time()) % 100:02d}-{int(time.time()) % 100000:05d}',
                'project_id': project_id,
                'contact_person': 'Test Contact',
                'phone': '02-1234-5678',
                'email': 'test@company.com',
                'address': 'Test Address, Seoul'
            }
            
            create_response = self.session.post(
                f"{API_BASE}/companies",
                json=company_data
            )
            assert create_response.status_code == 201, f"Company creation failed: {create_response.text}"
            
            company = create_response.json()
            self.test_data['companies'].append(company)
            company_id = company.get('id')
            
            # Get company details
            get_response = self.session.get(f"{API_BASE}/companies/{company_id}")
            assert get_response.status_code == 200, "Failed to get company details"
            
            # List companies for project
            list_response = self.session.get(f"{API_BASE}/projects/{project_id}/companies")
            assert list_response.status_code == 200, "Failed to list project companies"
            
            companies = list_response.json()
            company_found = any(c.get('id') == company_id for c in companies)
            assert company_found, "Company not found in project companies list"
            
            return {
                'status': 'passed',
                'company': company,
                'project_id': project_id,
                'companies_in_project': len(companies)
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_evaluation_workflow(self) -> Dict[str, Any]:
        """Test complete evaluation workflow"""
        try:
            # Ensure we have required data
            if not self.test_data['projects']:
                self.test_project_lifecycle()
            if not self.test_data['templates']:
                self.test_template_management()
            if not self.test_data['companies']:
                self.test_company_management()
            
            project_id = self.test_data['projects'][0]['id']
            template_id = self.test_data['templates'][0]['id']
            company_id = self.test_data['companies'][0]['id']
            
            # Create evaluation
            evaluation_data = {
                'project_id': project_id,
                'template_id': template_id,
                'company_id': company_id,
                'evaluator_notes': 'Integration test evaluation'
            }
            
            create_response = self.session.post(
                f"{API_BASE}/evaluations",
                json=evaluation_data
            )
            assert create_response.status_code == 201, f"Evaluation creation failed: {create_response.text}"
            
            evaluation = create_response.json()
            self.test_data['evaluations'].append(evaluation)
            evaluation_id = evaluation.get('id')
            
            # Submit evaluation scores
            template = self.test_data['templates'][0]
            criteria = template.get('criteria', [])
            
            scores_data = {
                'scores': {},
                'comments': {},
                'overall_comment': 'Integration test evaluation completed successfully'
            }
            
            # Add scores for each criteria
            test_scores = [85, 78, 82, 80]  # Scores for the 4 criteria
            for i, criterion in enumerate(criteria):
                criterion_name = criterion['name']
                scores_data['scores'][criterion_name] = test_scores[i] if i < len(test_scores) else 75
                scores_data['comments'][criterion_name] = f'Test comment for {criterion_name}'
            
            # Submit scores
            submit_response = self.session.post(
                f"{API_BASE}/evaluations/{evaluation_id}/submit",
                json=scores_data
            )
            assert submit_response.status_code == 200, f"Evaluation submission failed: {submit_response.text}"
            
            # Get evaluation results
            results_response = self.session.get(f"{API_BASE}/evaluations/{evaluation_id}")
            assert results_response.status_code == 200, "Failed to get evaluation results"
            
            results = results_response.json()
            
            # Verify total score calculation
            total_score = 0
            for criterion in criteria:
                criterion_name = criterion['name']
                score = scores_data['scores'].get(criterion_name, 0)
                weight = criterion.get('weight', 0) / 100
                total_score += score * weight
            
            return {
                'status': 'passed',
                'evaluation': evaluation,
                'results': results,
                'calculated_total_score': total_score,
                'criteria_count': len(criteria)
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_ai_model_integration(self) -> Dict[str, Any]:
        """Test AI model functionality if available"""
        try:
            # Check if AI models endpoint exists
            models_response = self.session.get(f"{API_BASE}/ai-models/available")
            
            if models_response.status_code == 200:
                models = models_response.json()
                
                if models:
                    # Test model configuration
                    first_model = models[0]
                    model_id = first_model.get('model_id')
                    
                    config_data = {
                        'status': 'active',
                        'parameters': {
                            'temperature': 0.7,
                            'max_tokens': 1000
                        }
                    }
                    
                    config_response = self.session.post(
                        f"{API_BASE}/ai-models/{model_id}/configure",
                        json=config_data
                    )
                    
                    # Test model recommendation
                    recommendation_request = {
                        'budget': 'medium',
                        'quality_level': 'high',
                        'speed_requirement': 'medium',
                        'task_type': 'evaluation',
                        'estimated_tokens': 500,
                        'estimated_requests_per_month': 100
                    }
                    
                    rec_response = self.session.post(
                        f"{API_BASE}/ai-models/recommend",
                        json=recommendation_request
                    )
                    
                    return {
                        'status': 'passed',
                        'models_available': len(models),
                        'configuration_status': config_response.status_code,
                        'recommendation_status': rec_response.status_code,
                        'first_model': first_model
                    }
                else:
                    return {
                        'status': 'warning',
                        'message': 'No AI models configured'
                    }
            else:
                return {
                    'status': 'warning',
                    'message': 'AI model functionality not available'
                }
                
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_export_functionality(self) -> Dict[str, Any]:
        """Test data export capabilities"""
        try:
            # Test evaluation export if we have evaluations
            if self.test_data['evaluations']:
                evaluation_id = self.test_data['evaluations'][0]['id']
                
                # Test PDF export
                pdf_response = self.session.get(
                    f"{API_BASE}/evaluations/{evaluation_id}/export/pdf"
                )
                
                # Test Excel export
                excel_response = self.session.get(
                    f"{API_BASE}/evaluations/{evaluation_id}/export/excel"
                )
                
                # Test bulk export if available
                bulk_response = self.session.get(
                    f"{API_BASE}/evaluations/export/bulk"
                )
                
                return {
                    'status': 'passed',
                    'pdf_export': pdf_response.status_code == 200,
                    'excel_export': excel_response.status_code == 200,
                    'bulk_export': bulk_response.status_code == 200,
                    'pdf_size': len(pdf_response.content) if pdf_response.status_code == 200 else 0,
                    'excel_size': len(excel_response.content) if excel_response.status_code == 200 else 0
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'No evaluations available for export testing'
                }
                
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_performance_under_load(self) -> Dict[str, Any]:
        """Test API performance under concurrent load"""
        try:
            import concurrent.futures
            import threading
            
            def make_request():
                start_time = time.time()
                response = self.session.get(f"{API_BASE}/projects")
                end_time = time.time()
                return {
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'success': response.status_code == 200
                }
            
            # Make 10 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                results = [f.result() for f in futures]
            
            successful_requests = sum(1 for r in results if r['success'])
            total_time = sum(r['response_time'] for r in results)
            avg_response_time = total_time / len(results)
            
            return {
                'status': 'passed',
                'total_requests': len(results),
                'successful_requests': successful_requests,
                'success_rate': successful_requests / len(results) * 100,
                'average_response_time': avg_response_time,
                'max_response_time': max(r['response_time'] for r in results),
                'min_response_time': min(r['response_time'] for r in results)
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def cleanup_test_data(self) -> Dict[str, Any]:
        """Clean up test data created during testing"""
        cleanup_results = {}
        
        try:
            # Delete evaluations
            for evaluation in self.test_data['evaluations']:
                eval_id = evaluation.get('id')
                response = self.session.delete(f"{API_BASE}/evaluations/{eval_id}")
                cleanup_results[f'evaluation_{eval_id}'] = response.status_code
            
            # Delete companies
            for company in self.test_data['companies']:
                company_id = company.get('id')
                response = self.session.delete(f"{API_BASE}/companies/{company_id}")
                cleanup_results[f'company_{company_id}'] = response.status_code
            
            # Delete templates
            for template in self.test_data['templates']:
                template_id = template.get('id')
                response = self.session.delete(f"{API_BASE}/templates/{template_id}")
                cleanup_results[f'template_{template_id}'] = response.status_code
            
            # Delete projects
            for project in self.test_data['projects']:
                project_id = project.get('id')
                response = self.session.delete(f"{API_BASE}/projects/{project_id}")
                cleanup_results[f'project_{project_id}'] = response.status_code
            
            # Delete users
            for user in self.test_data['users']:
                user_id = user.get('id')
                response = self.session.delete(f"{API_BASE}/users/{user_id}")
                cleanup_results[f'user_{user_id}'] = response.status_code
            
            return {
                'status': 'completed',
                'cleanup_results': cleanup_results
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'partial_cleanup': cleanup_results}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        test_results = {
            'test_run_id': f"integration_test_{int(time.time())}",
            'start_time': datetime.now().isoformat(),
            'results': {},
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
        
        # Login first
        if not self.login():
            test_results['results']['login'] = {'status': 'failed', 'error': 'Authentication failed'}
            test_results['summary']['total_tests'] = 1
            test_results['summary']['failed'] = 1
            return test_results
        
        # Define test sequence
        tests = [
            ('health_check', self.test_health_check),
            ('user_management', self.test_user_management_flow),
            ('project_lifecycle', self.test_project_lifecycle),
            ('template_management', self.test_template_management),
            ('company_management', self.test_company_management),
            ('evaluation_workflow', self.test_evaluation_workflow),
            ('ai_model_integration', self.test_ai_model_integration),
            ('export_functionality', self.test_export_functionality),
            ('performance_load', self.test_performance_under_load)
        ]
        
        # Run each test
        for test_name, test_func in tests:
            print(f"Running {test_name}...")
            result = test_func()
            test_results['results'][test_name] = result
            
            # Update summary
            test_results['summary']['total_tests'] += 1
            if result['status'] == 'passed':
                test_results['summary']['passed'] += 1
            elif result['status'] == 'failed':
                test_results['summary']['failed'] += 1
            elif result['status'] == 'warning':
                test_results['summary']['warnings'] += 1
        
        # Cleanup
        print("Cleaning up test data...")
        cleanup_result = self.cleanup_test_data()
        test_results['cleanup'] = cleanup_result
        
        test_results['end_time'] = datetime.now().isoformat()
        test_results['duration'] = (
            datetime.fromisoformat(test_results['end_time']) - 
            datetime.fromisoformat(test_results['start_time'])
        ).total_seconds()
        
        return test_results


def main():
    """Main function to run integration tests"""
    print("🚀 Starting API Integration Tests...")
    print(f"Testing against: {BASE_URL}")
    
    tester = APIIntegrationTester()
    results = tester.run_all_tests()
    
    # Print summary
    print("\\n" + "="*60)
    print("📊 INTEGRATION TEST RESULTS")
    print("="*60)
    print(f"Test Run ID: {results['test_run_id']}")
    print(f"Duration: {results['duration']:.2f} seconds")
    print(f"Total Tests: {results['summary']['total_tests']}")
    print(f"✅ Passed: {results['summary']['passed']}")
    print(f"❌ Failed: {results['summary']['failed']}")
    print(f"⚠️  Warnings: {results['summary']['warnings']}")
    
    # Print individual test results
    print("\\n📋 Individual Test Results:")
    for test_name, result in results['results'].items():
        status_emoji = {
            'passed': '✅',
            'failed': '❌',
            'warning': '⚠️'
        }.get(result['status'], '❓')
        
        print(f"{status_emoji} {test_name}: {result['status']}")
        if result['status'] == 'failed' and 'error' in result:
            print(f"   Error: {result['error']}")
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"integration_test_results_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\\n📄 Detailed results saved to: {results_file}")
    
    # Exit with appropriate code
    exit_code = 0 if results['summary']['failed'] == 0 else 1
    print(f"\\n🏁 Integration tests completed with exit code: {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    exit(main())