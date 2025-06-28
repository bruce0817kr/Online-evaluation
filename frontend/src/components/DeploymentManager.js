import React, { useState, useEffect } from 'react';
import './DeploymentManager.css';

const DeploymentManager = ({ user }) => {
  const [activeTab, setActiveTab] = useState('status'); // status, ports, deploy, history
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 상태 관리
  const [serviceStatus, setServiceStatus] = useState({});
  const [portStatus, setPortStatus] = useState(null);
  const [prerequisites, setPrerequisites] = useState(null);
  const [deploymentHistory, setDeploymentHistory] = useState([]);
  const [deploymentConfig, setDeploymentConfig] = useState({
    environment: 'development',
    force: false
  });
  
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019';

  useEffect(() => {
    loadInitialData();
    
    // 5초마다 상태 업데이트
    const interval = setInterval(() => {
      if (activeTab === 'status') {
        loadServiceStatus();
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [activeTab]);

  const loadInitialData = async () => {
    await Promise.all([
      loadServiceStatus(),
      loadPortStatus(),
      loadPrerequisites(),
      loadDeploymentHistory()
    ]);
  };

  const loadServiceStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/deployment/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setServiceStatus(data.services || {});
      }
    } catch (err) {
      console.error('서비스 상태 로드 실패:', err);
    }
  };

  const loadPortStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/deployment/ports/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setPortStatus(data.port_status);
      }
    } catch (err) {
      console.error('포트 상태 로드 실패:', err);
    }
  };

  const loadPrerequisites = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/deployment/prerequisites`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setPrerequisites(data.prerequisites);
      }
    } catch (err) {
      console.error('전제 조건 로드 실패:', err);
    }
  };

  const loadDeploymentHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/deployment/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setDeploymentHistory(data.history || []);
      }
    } catch (err) {
      console.error('배포 이력 로드 실패:', err);
    }
  };

  const executeDeploy = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/deployment/deploy`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(deploymentConfig)
      });

      if (response.ok) {
        const data = await response.json();
        alert(`배포가 시작되었습니다!\n환경: ${deploymentConfig.environment}`);
        
        // 상태 갱신
        setTimeout(() => {
          loadServiceStatus();
          loadDeploymentHistory();
        }, 2000);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '배포 실행에 실패했습니다');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generateScripts = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/deployment/generate-scripts?environment=${deploymentConfig.environment}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        alert('배포 스크립트가 생성되었습니다!');
      } else {
        throw new Error('스크립트 생성에 실패했습니다');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const checkPortConflicts = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/deployment/ports/conflicts`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.has_conflicts) {
          alert(`포트 충돌이 감지되었습니다:\n${JSON.stringify(data.conflicts, null, 2)}`);
        } else {
          alert('포트 충돌이 없습니다. 배포 가능합니다!');
        }
      }
    } catch (err) {
      setError('포트 충돌 검사 실패');
    }
  };

  const rollbackDeployment = async () => {
    if (!window.confirm('정말로 이전 배포로 롤백하시겠습니까?')) {
      return;
    }

    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/deployment/rollback`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        alert('롤백이 성공적으로 완료되었습니다!');
        loadServiceStatus();
      } else {
        throw new Error('롤백 실행에 실패했습니다');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    if (status === true) return '✅';
    if (status === false) return '❌';
    return '⚠️';
  };

  const getServiceStatusIcon = (service) => {
    if (service.healthy) return '🟢';
    if (service.running) return '🟡';
    return '🔴';
  };

  const formatDate = (dateString) => {
    if (!dateString) return '알 수 없음';
    try {
      return new Date(dateString).toLocaleString('ko-KR');
    } catch {
      return '알 수 없음';
    }
  };

  if (user.role !== 'admin') {
    return (
      <div className="deployment-manager">
        <div className="access-denied">
          <h2>🚫 접근 권한 없음</h2>
          <p>배포 관리 기능은 관리자만 사용할 수 있습니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="deployment-manager">
      <div className="manager-header">
        <h2>🚀 배포 관리 시스템</h2>
        <p>원클릭 배포 및 포트 관리</p>
      </div>

      {error && (
        <div className="error-alert">
          <span className="error-icon">⚠️</span>
          {error}
          <button onClick={() => setError(null)} className="close-error">✕</button>
        </div>
      )}

      {/* 탭 네비게이션 */}
      <div className="tab-navigation">
        <button
          className={`tab-btn ${activeTab === 'status' ? 'active' : ''}`}
          onClick={() => setActiveTab('status')}
        >
          📊 서비스 상태
        </button>
        <button
          className={`tab-btn ${activeTab === 'ports' ? 'active' : ''}`}
          onClick={() => setActiveTab('ports')}
        >
          🔌 포트 관리
        </button>
        <button
          className={`tab-btn ${activeTab === 'deploy' ? 'active' : ''}`}
          onClick={() => setActiveTab('deploy')}
        >
          🚀 배포 실행
        </button>
        <button
          className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          📜 배포 이력
        </button>
      </div>

      <div className="tab-content">
        {/* 서비스 상태 탭 */}
        {activeTab === 'status' && (
          <div className="status-tab">
            <h3>서비스 상태 모니터링</h3>
            <p>현재 실행 중인 서비스들의 상태를 실시간으로 확인합니다.</p>

            <div className="services-grid">
              {Object.entries(serviceStatus).map(([serviceName, service]) => (
                <div key={serviceName} className={`service-card ${service.healthy ? 'healthy' : service.running ? 'running' : 'stopped'}`}>
                  <div className="service-header">
                    <span className="service-status-icon">{getServiceStatusIcon(service)}</span>
                    <h4>{service.name}</h4>
                  </div>
                  
                  <div className="service-info">
                    <p><strong>포트:</strong> {service.port || '할당되지 않음'}</p>
                    <p><strong>URL:</strong> <a href={service.url} target="_blank" rel="noopener noreferrer">{service.url}</a></p>
                    <p><strong>상태:</strong> {service.running ? '실행 중' : '중지됨'}</p>
                    <p><strong>헬스체크:</strong> {service.healthy ? '정상' : '실패'}</p>
                    {service.container_status && (
                      <p><strong>컨테이너:</strong> {service.container_status}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* 전제 조건 상태 */}
            {prerequisites && (
              <div className="prerequisites-section">
                <h4>배포 전제 조건</h4>
                <div className="prerequisites-grid">
                  {Object.entries(prerequisites).map(([key, value]) => (
                    <div key={key} className={`prerequisite-item ${value ? 'satisfied' : 'missing'}`}>
                      <span className="prerequisite-icon">{getStatusIcon(value)}</span>
                      <span className="prerequisite-name">
                        {key === 'docker' && 'Docker'}
                        {key === 'docker_compose' && 'Docker Compose'}
                        {key === 'env_file' && '환경 변수 파일'}
                        {key === 'docker_compose_file' && 'Docker Compose 파일'}
                        {key === 'port_availability' && '포트 가용성'}
                        {key === 'disk_space' && '디스크 공간'}
                        {key === 'memory' && '메모리'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 포트 관리 탭 */}
        {activeTab === 'ports' && (
          <div className="ports-tab">
            <h3>포트 관리</h3>
            <p>서비스별 포트 할당 및 충돌 검사를 수행합니다.</p>

            <div className="port-actions">
              <button onClick={checkPortConflicts} className="check-conflicts-btn">
                🔍 포트 충돌 검사
              </button>
              <button onClick={loadPortStatus} className="refresh-btn">
                🔄 새로고침
              </button>
            </div>

            {portStatus && (
              <div className="port-status-grid">
                <div className="port-section">
                  <h4>할당된 포트</h4>
                  <div className="allocated-ports">
                    {Object.entries(portStatus.allocated_ports).map(([service, port]) => (
                      <div key={service} className="port-item">
                        <span className="service-name">{service}</span>
                        <span className="port-number">:{port}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="port-section">
                  <h4>예약된 포트</h4>
                  <div className="reserved-ports">
                    {portStatus.reserved_ports.map(port => (
                      <span key={port} className="reserved-port">{port}</span>
                    ))}
                  </div>
                </div>

                <div className="port-section">
                  <h4>활성 연결</h4>
                  <div className="active-connections">
                    {portStatus.active_connections.slice(0, 10).map((conn, index) => (
                      <div key={index} className="connection-item">
                        <span className="conn-port">:{conn.port}</span>
                        <span className="conn-status">{conn.status}</span>
                        <span className="conn-pid">PID: {conn.pid}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 배포 실행 탭 */}
        {activeTab === 'deploy' && (
          <div className="deploy-tab">
            <h3>배포 실행</h3>
            <p>시스템을 선택한 환경으로 배포합니다.</p>

            <div className="deployment-config">
              <h4>배포 설정</h4>
              
              <div className="config-item">
                <label>배포 환경</label>
                <select
                  value={deploymentConfig.environment}
                  onChange={(e) => setDeploymentConfig(prev => ({
                    ...prev,
                    environment: e.target.value
                  }))}
                >
                  <option value="development">개발 (Development)</option>
                  <option value="staging">스테이징 (Staging)</option>
                  <option value="production">운영 (Production)</option>
                </select>
              </div>

              <div className="config-item checkbox-item">
                <label>
                  <input
                    type="checkbox"
                    checked={deploymentConfig.force}
                    onChange={(e) => setDeploymentConfig(prev => ({
                      ...prev,
                      force: e.target.checked
                    }))}
                  />
                  전제 조건 무시 (Force Deploy)
                </label>
                <small>⚠️ 주의: 전제 조건을 무시하면 배포가 실패할 수 있습니다.</small>
              </div>
            </div>

            <div className="deployment-actions">
              <button
                onClick={generateScripts}
                disabled={loading}
                className="generate-scripts-btn"
              >
                📝 배포 스크립트 생성
              </button>
              
              <button
                onClick={executeDeploy}
                disabled={loading}
                className="deploy-btn"
              >
                {loading ? '⏳ 배포 중...' : '🚀 배포 실행'}
              </button>

              <button
                onClick={rollbackDeployment}
                disabled={loading}
                className="rollback-btn"
              >
                ⏪ 롤백
              </button>
            </div>

            <div className="deployment-info">
              <h4>배포 프로세스</h4>
              <ol>
                <li>전제 조건 확인 (Docker, 포트, 리소스)</li>
                <li>환경 변수 파일 생성</li>
                <li>Docker Compose 설정 생성</li>
                <li>배포 스크립트 생성</li>
                <li>Docker 이미지 빌드 및 컨테이너 실행</li>
                <li>헬스체크 및 상태 확인</li>
              </ol>
            </div>
          </div>
        )}

        {/* 배포 이력 탭 */}
        {activeTab === 'history' && (
          <div className="history-tab">
            <h3>배포 이력</h3>
            <p>과거 배포 작업의 기록을 확인합니다.</p>

            <div className="history-list">
              {deploymentHistory.length === 0 ? (
                <div className="empty-history">
                  <p>배포 이력이 없습니다.</p>
                </div>
              ) : (
                deploymentHistory.map((deployment, index) => (
                  <div key={index} className={`history-item ${deployment.status}`}>
                    <div className="history-header">
                      <span className={`status-badge ${deployment.status}`}>
                        {deployment.status === 'success' && '✅ 성공'}
                        {deployment.status === 'failed' && '❌ 실패'}
                        {deployment.status === 'pending' && '⏳ 진행 중'}
                      </span>
                      <span className="deployment-time">
                        {formatDate(deployment.started_at)}
                      </span>
                    </div>

                    <div className="history-details">
                      <p><strong>환경:</strong> {deployment.environment}</p>
                      {deployment.completed_at && (
                        <p><strong>완료 시간:</strong> {formatDate(deployment.completed_at)}</p>
                      )}
                      
                      {deployment.steps && (
                        <div className="deployment-steps">
                          <h5>실행 단계:</h5>
                          {Object.entries(deployment.steps).map(([step, result]) => (
                            <div key={step} className="step-item">
                              <span className="step-icon">{getStatusIcon(result)}</span>
                              <span className="step-name">{step}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {deployment.error && (
                        <div className="deployment-error">
                          <h5>오류:</h5>
                          <p>{deployment.error}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DeploymentManager;