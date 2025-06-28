import React, { useState, useEffect, useRef, useCallback } from 'react';
import './SecurePDFViewer.css';

const SecurePDFViewer = ({ 
  fileUrl, 
  fileName, 
  onClose,
  user,
  evaluationId = null,
  companyId = null 
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pdfData, setPdfData] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [scale, setScale] = useState(1.0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  const viewerRef = useRef(null);
  const canvasRef = useRef(null);
  const pdfDocRef = useRef(null);
  
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019';

  // 보안 이벤트 차단
  const preventSecurityViolations = useCallback(() => {
    // 우클릭 방지
    const preventContextMenu = (e) => {
      e.preventDefault();
      return false;
    };

    // 키보드 단축키 차단
    const preventKeyboardShortcuts = (e) => {
      // Ctrl+S (저장), Ctrl+P (인쇄), Ctrl+A (전체선택), F12 (개발자도구)
      if (
        (e.ctrlKey && (e.key === 's' || e.key === 'p' || e.key === 'a')) ||
        e.key === 'F12' ||
        (e.ctrlKey && e.shiftKey && e.key === 'I') || // 개발자도구
        (e.ctrlKey && e.shiftKey && e.key === 'C') || // 요소검사
        e.key === 'PrintScreen' // 프린트스크린
      ) {
        e.preventDefault();
        alert('보안상의 이유로 이 기능은 사용할 수 없습니다.');
        return false;
      }
    };

    // 드래그 방지
    const preventDrag = (e) => {
      e.preventDefault();
      return false;
    };

    // 텍스트 선택 방지
    const preventSelection = (e) => {
      e.preventDefault();
      return false;
    };

    // 이벤트 리스너 추가
    document.addEventListener('contextmenu', preventContextMenu);
    document.addEventListener('keydown', preventKeyboardShortcuts);
    document.addEventListener('dragstart', preventDrag);
    document.addEventListener('selectstart', preventSelection);
    
    // 개발자 도구 감지 (간단한 방법)
    let devtools = { open: false };
    const threshold = 160;
    
    const detectDevTools = () => {
      if (window.outerHeight - window.innerHeight > threshold || 
          window.outerWidth - window.innerWidth > threshold) {
        if (!devtools.open) {
          devtools.open = true;
          alert('보안상의 이유로 개발자 도구 사용이 감지되었습니다.');
          if (onClose) onClose();
        }
      } else {
        devtools.open = false;
      }
    };

    const devToolsInterval = setInterval(detectDevTools, 500);

    // 정리 함수 반환
    return () => {
      document.removeEventListener('contextmenu', preventContextMenu);
      document.removeEventListener('keydown', preventKeyboardShortcuts);
      document.removeEventListener('dragstart', preventDrag);
      document.removeEventListener('selectstart', preventSelection);
      clearInterval(devToolsInterval);
    };
  }, [onClose]);

  // PDF.js 동적 로드
  const loadPDFJS = useCallback(async () => {
    if (window.pdfjsLib) return window.pdfjsLib;

    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
      script.onload = () => {
        window.pdfjsLib.GlobalWorkerOptions.workerSrc = 
          'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        resolve(window.pdfjsLib);
      };
      document.head.appendChild(script);
    });
  }, []);

  // 보안 PDF 데이터 로드
  const loadSecurePDF = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('인증이 필요합니다.');
      }

      // 보안 PDF 엔드포인트 호출
      const response = await fetch(`${BACKEND_URL}/api/files/secure-pdf-view`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          file_url: fileUrl,
          evaluation_id: evaluationId,
          company_id: companyId
        })
      });

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('PDF 조회 권한이 없습니다.');
        }
        throw new Error(`PDF 로드 실패: ${response.status}`);
      }

      const arrayBuffer = await response.arrayBuffer();
      
      // PDF.js로 PDF 로드
      const pdfjsLib = await loadPDFJS();
      const pdf = await pdfjsLib.getDocument({
        data: arrayBuffer,
        // 추가 보안 옵션
        disableRange: true,
        disableStream: true,
        disableAutoFetch: true
      }).promise;

      pdfDocRef.current = pdf;
      setTotalPages(pdf.numPages);
      setPdfData(arrayBuffer);
      
    } catch (err) {
      console.error('PDF 로드 오류:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [fileUrl, evaluationId, companyId, loadPDFJS, BACKEND_URL]);

  // PDF 페이지 렌더링
  const renderPage = useCallback(async (pageNumber) => {
    if (!pdfDocRef.current || !canvasRef.current) return;

    try {
      const page = await pdfDocRef.current.getPage(pageNumber);
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');

      const viewport = page.getViewport({ scale });
      canvas.height = viewport.height;
      canvas.width = viewport.width;

      const renderContext = {
        canvasContext: context,
        viewport: viewport,
      };

      await page.render(renderContext).promise;
      
      // 워터마크 추가
      addWatermark(context, canvas.width, canvas.height);
      
    } catch (err) {
      console.error('페이지 렌더링 오류:', err);
      setError('페이지를 렌더링할 수 없습니다.');
    }
  }, [scale]);

  // 워터마크 추가
  const addWatermark = useCallback((context, width, height) => {
    context.save();
    context.globalAlpha = 0.1;
    context.font = '48px Arial';
    context.fillStyle = '#000000';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    
    const watermarkText = `${user?.user_name || 'USER'} - ${new Date().toLocaleDateString()}`;
    
    // 여러 위치에 워터마크 추가
    for (let i = 0; i < 3; i++) {
      for (let j = 0; j < 2; j++) {
        const x = (width / 3) * (i + 0.5);
        const y = (height / 2) * (j + 0.5);
        context.fillText(watermarkText, x, y);
      }
    }
    
    context.restore();
  }, [user]);

  // 페이지 변경
  const changePage = useCallback((newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  }, [totalPages]);

  // 확대/축소
  const changeScale = useCallback((newScale) => {
    if (newScale >= 0.5 && newScale <= 3.0) {
      setScale(newScale);
    }
  }, []);

  // 전체화면 토글
  const toggleFullscreen = useCallback(() => {
    if (!isFullscreen) {
      if (viewerRef.current?.requestFullscreen) {
        viewerRef.current.requestFullscreen();
        setIsFullscreen(true);
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
        setIsFullscreen(false);
      }
    }
  }, [isFullscreen]);

  // 컴포넌트 마운트 시 보안 설정 및 PDF 로드
  useEffect(() => {
    const cleanup = preventSecurityViolations();
    loadSecurePDF();
    
    return cleanup;
  }, [preventSecurityViolations, loadSecurePDF]);

  // 페이지 변경 시 렌더링
  useEffect(() => {
    if (pdfDocRef.current) {
      renderPage(currentPage);
    }
  }, [currentPage, scale, renderPage]);

  // 전체화면 이벤트 리스너
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  if (loading) {
    return (
      <div className="secure-pdf-viewer loading">
        <div className="loading-content">
          <div className="spinner"></div>
          <p>보안 PDF를 로드하는 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="secure-pdf-viewer error">
        <div className="error-content">
          <h3>⚠️ PDF 로드 오류</h3>
          <p>{error}</p>
          <button onClick={onClose} className="close-btn">
            닫기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`secure-pdf-viewer ${isFullscreen ? 'fullscreen' : ''}`} ref={viewerRef}>
      {/* 보안 경고 오버레이 */}
      <div className="security-overlay">
        <div className="security-warning">
          🔒 보안 문서 - 저장, 복사, 캡처 금지
        </div>
      </div>

      {/* 뷰어 헤더 */}
      <div className="viewer-header">
        <div className="file-info">
          <h3>{fileName}</h3>
          <span className="page-info">
            {currentPage} / {totalPages} 페이지
          </span>
        </div>
        
        <div className="viewer-controls">
          {/* 페이지 네비게이션 */}
          <div className="page-controls">
            <button 
              onClick={() => changePage(currentPage - 1)}
              disabled={currentPage <= 1}
              className="nav-btn"
            >
              ◀
            </button>
            <input
              type="number"
              value={currentPage}
              onChange={(e) => changePage(parseInt(e.target.value))}
              min="1"
              max={totalPages}
              className="page-input"
            />
            <button 
              onClick={() => changePage(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="nav-btn"
            >
              ▶
            </button>
          </div>

          {/* 확대/축소 */}
          <div className="zoom-controls">
            <button 
              onClick={() => changeScale(scale - 0.1)}
              disabled={scale <= 0.5}
              className="zoom-btn"
            >
              -
            </button>
            <span className="zoom-level">{Math.round(scale * 100)}%</span>
            <button 
              onClick={() => changeScale(scale + 0.1)}
              disabled={scale >= 3.0}
              className="zoom-btn"
            >
              +
            </button>
            <button 
              onClick={() => changeScale(1.0)}
              className="zoom-reset"
            >
              100%
            </button>
          </div>

          {/* 기타 컨트롤 */}
          <div className="view-controls">
            <button onClick={toggleFullscreen} className="fullscreen-btn">
              {isFullscreen ? '⚟' : '⚞'}
            </button>
            <button onClick={onClose} className="close-btn">
              ✕
            </button>
          </div>
        </div>
      </div>

      {/* PDF 캔버스 */}
      <div className="pdf-container">
        <canvas 
          ref={canvasRef}
          className="pdf-canvas"
        />
      </div>

      {/* 보안 메시지 */}
      <div className="security-footer">
        <span>🔐 이 문서는 보안이 적용되어 있습니다. 무단 복제, 저장, 캡처를 금지합니다.</span>
        <span>👤 사용자: {user?.user_name} | 📅 열람일: {new Date().toLocaleString()}</span>
      </div>
    </div>
  );
};

export default SecurePDFViewer;