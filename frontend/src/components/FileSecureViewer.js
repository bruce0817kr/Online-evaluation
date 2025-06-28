import React, { useState, useEffect } from 'react';
import SecurePDFViewer from './SecurePDFViewer.js';
import './FileSecureViewer.css';

const FileSecureViewer = ({ 
  files, 
  user, 
  evaluationId = null,
  companyId = null,
  projectId = null,
  onClose 
}) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fileList, setFileList] = useState([]);
  const [availableProjects, setAvailableProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(projectId || '');

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019';

  useEffect(() => {
    loadProjects();
    if (files && Array.isArray(files)) {
      setFileList(files);
    } else if (typeof files === 'string') {
      // 단일 파일 URL인 경우
      setFileList([{ url: files, name: '문서.pdf' }]);
    } else {
      // 파일 목록을 API로 가져오기
      loadFileList();
    }
  }, [files, evaluationId, companyId, projectId]);

  useEffect(() => {
    // 프로젝트 선택이 변경되면 파일 목록 새로고침
    if (!files || (!Array.isArray(files) && typeof files !== 'string')) {
      loadFileList();
    }
  }, [selectedProject]);

  const loadProjects = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/projects`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAvailableProjects(data);
      }
    } catch (err) {
      console.error('프로젝트 목록 로드 실패:', err);
    }
  };

  const loadFileList = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams();
      if (evaluationId) params.append('evaluation_id', evaluationId);
      if (companyId) params.append('company_id', companyId);
      if (selectedProject) params.append('project_id', selectedProject);

      const response = await fetch(`${BACKEND_URL}/api/files?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setFileList(data.files || []);
      } else {
        throw new Error('파일 목록을 불러올 수 없습니다');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getFileIcon = (fileName) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf':
        return '📄';
      case 'doc':
      case 'docx':
        return '📝';
      case 'xls':
      case 'xlsx':
        return '📊';
      case 'ppt':
      case 'pptx':
        return '📽️';
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return '🖼️';
      default:
        return '📎';
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '알 수 없음';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    if (!dateString) return '알 수 없음';
    try {
      return new Date(dateString).toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return '알 수 없음';
    }
  };

  const handleFileClick = (file) => {
    const fileName = file.name || file.file_name || '문서';
    const fileUrl = file.url || file.file_path || file.file_url;
    
    // PDF 파일만 보안 뷰어로 열기
    if (fileName.toLowerCase().endsWith('.pdf')) {
      setSelectedFile({
        url: fileUrl,
        name: fileName,
        ...file
      });
    } else {
      // PDF가 아닌 파일은 다운로드 또는 다른 처리
      alert('현재 PDF 파일만 보안 뷰어에서 열람할 수 있습니다.');
    }
  };

  const canViewFile = (file) => {
    // 권한 확인 로직
    if (user.role === 'admin') return true;
    if (user.role === 'secretary') return true;
    if (user.role === 'evaluator') {
      // 평가위원은 할당된 평가의 파일만 열람 가능
      return evaluationId || companyId;
    }
    return false;
  };

  if (selectedFile) {
    return (
      <SecurePDFViewer
        fileUrl={selectedFile.url}
        fileName={selectedFile.name}
        user={user}
        evaluationId={evaluationId}
        companyId={companyId}
        onClose={() => setSelectedFile(null)}
      />
    );
  }

  return (
    <div className="file-secure-viewer">
      <div className="viewer-header">
        <h3>📁 파일 목록</h3>
        {onClose && (
          <button onClick={onClose} className="close-btn">
            ✕
          </button>
        )}
      </div>

      {/* 프로젝트 선택 */}
      <div className="project-selector">
        <div className="selector-group">
          <label htmlFor="project-select">📂 프로젝트 선택:</label>
          <select 
            id="project-select"
            value={selectedProject} 
            onChange={(e) => setSelectedProject(e.target.value)}
            className="project-select"
          >
            <option value="">전체 프로젝트</option>
            {availableProjects.map(project => (
              <option key={project.id || project._id} value={project.id || project._id}>
                {project.name}
              </option>
            ))}
          </select>
          <span className="file-count">
            ({fileList.length}개 파일)
          </span>
        </div>
      </div>

      {error && (
        <div className="error-alert">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>파일 목록을 불러오는 중...</p>
        </div>
      ) : (
        <div className="file-list">
          {fileList.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📂</div>
              <p>표시할 파일이 없습니다.</p>
            </div>
          ) : (
            <div className="file-grid">
              {fileList.map((file, index) => {
                const fileName = file.name || file.file_name || `파일_${index + 1}`;
                const canView = canViewFile(file);
                
                return (
                  <div 
                    key={index}
                    className={`file-item ${canView ? 'clickable' : 'disabled'}`}
                    onClick={() => canView && handleFileClick(file)}
                  >
                    <div className="file-icon">
                      {getFileIcon(fileName)}
                    </div>
                    
                    <div className="file-info">
                      <h4 className="file-name" title={fileName}>
                        {fileName.length > 25 ? fileName.substring(0, 25) + '...' : fileName}
                      </h4>
                      
                      <div className="file-details">
                        <span className="file-size">
                          {formatFileSize(file.size || file.file_size)}
                        </span>
                        <span className="file-date">
                          {formatDate(file.uploaded_at || file.created_at)}
                        </span>
                      </div>
                      
                      {file.company_name && (
                        <div className="file-company">
                          🏢 {file.company_name}
                        </div>
                      )}
                      
                      {file.file_type && (
                        <div className="file-type-badge">
                          {file.file_type}
                        </div>
                      )}
                    </div>

                    <div className="file-actions">
                      {canView ? (
                        fileName.toLowerCase().endsWith('.pdf') ? (
                          <span className="action-hint">🔍 클릭하여 보기</span>
                        ) : (
                          <span className="action-hint">📎 다운로드만 가능</span>
                        )
                      ) : (
                        <span className="action-hint disabled">🚫 권한 없음</span>
                      )}
                    </div>

                    {!canView && (
                      <div className="access-denied-overlay">
                        <span>🔒</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      <div className="viewer-footer">
        <div className="security-notice">
          🔒 모든 파일은 보안이 적용되어 있습니다. 무단 복제나 유출을 금지합니다.
        </div>
        <div className="user-info">
          👤 {user?.user_name} | 📅 {new Date().toLocaleString()}
        </div>
      </div>
    </div>
  );
};

export default FileSecureViewer;