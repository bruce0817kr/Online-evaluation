#!/usr/bin/env python3
"""
Test Environment Fix Script
자동으로 테스트 환경 설정 문제를 해결하는 스크립트
"""

import os
import subprocess
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

class TestEnvironmentFixer:
    def __init__(self):
        self.fixes_applied = []
        self.errors_encountered = []
        self.start_time = datetime.now()
        
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
        
    def run_command(self, cmd, cwd=None, check=False):
        """안전한 명령어 실행"""
        try:
            result = subprocess.run(
                cmd, shell=True, cwd=cwd, 
                capture_output=True, text=True, timeout=120
            )
            return result
        except subprocess.TimeoutExpired:
            self.log(f"Command timed out: {cmd}", "ERROR")
            return None
        except Exception as e:
            self.log(f"Command failed: {cmd} - {str(e)}", "ERROR")
            return None
    
    def fix_python_path(self):
        """Python 경로 문제 해결"""
        self.log("Python 경로 확인 및 수정...")
        
        # Python3 경로 확인
        python3_result = self.run_command("which python3")
        if python3_result and python3_result.returncode == 0:
            python3_path = python3_result.stdout.strip()
            self.log(f"Python3 found at: {python3_path}")
            
            # python 명령어 확인
            python_result = self.run_command("which python")
            if not python_result or python_result.returncode != 0:
                self.log("Creating python symlink...")
                
                # WSL 환경에서 사용자 bin 디렉터리 생성
                user_bin = os.path.expanduser("~/.local/bin")
                os.makedirs(user_bin, exist_ok=True)
                
                # 심볼릭 링크 생성
                python_link = os.path.join(user_bin, "python")
                if not os.path.exists(python_link):
                    try:
                        os.symlink(python3_path, python_link)
                        self.log(f"Created symlink: {python_link} -> {python3_path}")
                        self.fixes_applied.append("Python symlink created")
                    except OSError as e:
                        self.log(f"Failed to create symlink: {e}", "WARNING")
                
                # PATH 업데이트 제안
                self.log("Add ~/.local/bin to PATH if not already present")
                self.fixes_applied.append("Python path configuration")
        else:
            self.log("Python3 not found!", "ERROR")
            self.errors_encountered.append("Python3 not installed")
    
    def install_missing_dependencies(self):
        """누락된 의존성 설치"""
        self.log("Python 의존성 확인 및 설치...")
        
        # 필수 Python 패키지
        required_packages = [
            "psutil",
            "playwright", 
            "pyyaml",
            "aiofiles",
            "websockets"
        ]
        
        for package in required_packages:
            self.log(f"Checking {package}...")
            check_result = self.run_command(f"python3 -c 'import {package}'")
            
            if not check_result or check_result.returncode != 0:
                self.log(f"Installing {package}...")
                install_result = self.run_command(f"pip3 install {package}")
                
                if install_result and install_result.returncode == 0:
                    self.log(f"✅ {package} installed successfully")
                    self.fixes_applied.append(f"Installed {package}")
                else:
                    self.log(f"❌ Failed to install {package}", "ERROR")
                    self.errors_encountered.append(f"Failed to install {package}")
            else:
                self.log(f"✅ {package} already installed")
        
        # Playwright 브라우저 설치
        self.log("Installing Playwright browsers...")
        playwright_result = self.run_command("python3 -m playwright install")
        if playwright_result and playwright_result.returncode == 0:
            self.log("✅ Playwright browsers installed")
            self.fixes_applied.append("Playwright browsers installed")
        else:
            self.log("❌ Failed to install Playwright browsers", "ERROR")
            self.errors_encountered.append("Playwright browser installation failed")
    
    def fix_jsx_configuration(self):
        """JSX/Babel 설정 수정"""
        self.log("JSX/Babel 설정 확인 및 수정...")
        
        frontend_dir = "frontend"
        if not os.path.exists(frontend_dir):
            self.log("Frontend directory not found", "ERROR")
            self.errors_encountered.append("Frontend directory missing")
            return
        
        # package.json 확인
        package_json_path = os.path.join(frontend_dir, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                # Babel 설정 확인 및 추가
                has_babel_react = False
                dev_deps = package_data.get('devDependencies', {})
                deps = package_data.get('dependencies', {})
                
                # React preset 확인
                if '@babel/preset-react' in dev_deps or '@babel/preset-react' in deps:
                    has_babel_react = True
                    self.log("✅ @babel/preset-react found in dependencies")
                else:
                    self.log("Installing @babel/preset-react...")
                    install_result = self.run_command(
                        "npm install --save-dev @babel/preset-react @babel/core @babel/preset-env",
                        cwd=frontend_dir
                    )
                    
                    if install_result and install_result.returncode == 0:
                        self.log("✅ Babel React preset installed")
                        self.fixes_applied.append("Babel React preset installed")
                        has_babel_react = True
                    else:
                        self.log("❌ Failed to install Babel React preset", "ERROR")
                        self.errors_encountered.append("Babel installation failed")
                
                # .babelrc 또는 babel.config.js 생성
                babel_config_path = os.path.join(frontend_dir, ".babelrc")
                babel_config_js_path = os.path.join(frontend_dir, "babel.config.js")
                
                if not os.path.exists(babel_config_path) and not os.path.exists(babel_config_js_path):
                    babel_config = {
                        "presets": [
                            "@babel/preset-env",
                            ["@babel/preset-react", {"runtime": "automatic"}]
                        ],
                        "plugins": []
                    }
                    
                    with open(babel_config_path, 'w') as f:
                        json.dump(babel_config, f, indent=2)
                    
                    self.log("✅ Created .babelrc configuration")
                    self.fixes_applied.append("Created Babel configuration")
                else:
                    self.log("✅ Babel configuration already exists")
                
            except Exception as e:
                self.log(f"Failed to process package.json: {e}", "ERROR")
                self.errors_encountered.append("Package.json processing failed")
        else:
            self.log("package.json not found in frontend directory", "ERROR")
            self.errors_encountered.append("Frontend package.json missing")
    
    def check_and_fix_test_setup(self):
        """테스트 설정 확인 및 수정"""
        self.log("테스트 설정 확인...")
        
        # Jest 설정 확인 (frontend)
        frontend_package_json = "frontend/package.json"
        if os.path.exists(frontend_package_json):
            try:
                with open(frontend_package_json, 'r') as f:
                    package_data = json.load(f)
                
                # Jest 설정이 있는지 확인
                if 'jest' not in package_data:
                    jest_config = {
                        "testEnvironment": "jsdom",
                        "setupFilesAfterEnv": ["<rootDir>/src/setupTests.js"],
                        "moduleNameMapping": {
                            "\\.(css|less|scss|sass)$": "identity-obj-proxy"
                        },
                        "transform": {
                            "^.+\\.(js|jsx)$": "babel-jest"
                        }
                    }
                    
                    package_data['jest'] = jest_config
                    
                    with open(frontend_package_json, 'w') as f:
                        json.dump(package_data, f, indent=2)
                    
                    self.log("✅ Jest configuration added")
                    self.fixes_applied.append("Jest configuration updated")
                else:
                    self.log("✅ Jest configuration already exists")
                
            except Exception as e:
                self.log(f"Failed to update Jest config: {e}", "ERROR")
                self.errors_encountered.append("Jest configuration failed")
        
        # setupTests.js 생성
        setup_tests_path = "frontend/src/setupTests.js"
        if not os.path.exists(setup_tests_path):
            os.makedirs(os.path.dirname(setup_tests_path), exist_ok=True)
            
            setup_content = '''// jest-dom adds custom jest matchers for asserting on DOM nodes.
import '@testing-library/jest-dom';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock sessionStorage  
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.sessionStorage = sessionStorageMock;

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});
'''
            
            with open(setup_tests_path, 'w') as f:
                f.write(setup_content)
            
            self.log("✅ Created setupTests.js")
            self.fixes_applied.append("Created test setup file")
    
    def create_environment_report(self):
        """환경 설정 보고서 생성"""
        self.log("환경 설정 보고서 생성...")
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        report = {
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration,
            "fixes_applied": self.fixes_applied,
            "errors_encountered": self.errors_encountered,
            "success_rate": len(self.fixes_applied) / (len(self.fixes_applied) + len(self.errors_encountered)) * 100 if (self.fixes_applied or self.errors_encountered) else 100,
            "status": "SUCCESS" if not self.errors_encountered else "PARTIAL_SUCCESS" if self.fixes_applied else "FAILED"
        }
        
        report_file = f"environment_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 콘솔 출력
        print("\n" + "="*60)
        print("🔧 환경 설정 수정 결과")
        print("="*60)
        print(f"⏰ 실행 시간: {duration:.1f}초")
        print(f"📊 성공률: {report['success_rate']:.1f}%")
        print(f"📄 보고서: {report_file}")
        
        if self.fixes_applied:
            print("\n✅ 적용된 수정사항:")
            for i, fix in enumerate(self.fixes_applied, 1):
                print(f"  {i}. {fix}")
        
        if self.errors_encountered:
            print("\n❌ 발생한 오류:")
            for i, error in enumerate(self.errors_encountered, 1):
                print(f"  {i}. {error}")
        
        # 다음 단계 안내
        print("\n🚀 다음 단계:")
        if not self.errors_encountered:
            print("  1. 새 터미널 세션 시작 (PATH 적용)")
            print("  2. python3 quick_test_validator.py 실행")
            print("  3. python3 ultra_comprehensive_test_runner.py 실행")
        else:
            print("  1. 오류사항을 수동으로 해결")
            print("  2. 이 스크립트를 다시 실행")
            print("  3. 문제가 지속되면 README.md 참조")
        
        print("="*60)
        
        return report_file, report['status']
    
    def run_all_fixes(self):
        """모든 수정사항 실행"""
        print("🚀 테스트 환경 자동 수정 시작")
        print("="*60)
        
        self.fix_python_path()
        self.install_missing_dependencies()
        self.fix_jsx_configuration()
        self.check_and_fix_test_setup()
        
        return self.create_environment_report()

def main():
    """메인 실행 함수"""
    fixer = TestEnvironmentFixer()
    report_file, status = fixer.run_all_fixes()
    
    # 성공 여부에 따른 종료 코드
    if status == "SUCCESS":
        sys.exit(0)
    elif status == "PARTIAL_SUCCESS":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()