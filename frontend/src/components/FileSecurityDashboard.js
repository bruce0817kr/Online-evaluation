import React, { useState, useEffect } from 'react';

const FileSecurityDashboard = ({ user }) => {
  const [accessLogs, setAccessLogs] = useState([]);
  const [securityAnalytics, setSecurityAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    file_id: '',
    user_id: '',
    action: '',
    start_date: '',
    end_date: '',
    limit: 100
  });

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019';

  // 권한 검사
  if (!user || user.role !== 'admin') {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">파일 보안 대시보드</h2>
        <p className="text-gray-600">이 기능은 관리자만 사용할 수 있습니다.</p>
      </div>
    );
  }

  // 접근 로그 조회
  const fetchAccessLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await fetch(`${BACKEND_URL}/api/files/access-logs?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAccessLogs(data.logs || []);
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || '접근 로그 조회에 실패했습니다.');
      }
    } catch (err) {
      const userFriendlyMessage = err.message.includes('Failed to fetch') 
        ? '서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.'
        : err.message;
      setError(userFriendlyMessage);
      console.error('접근 로그 조회 오류:', err);
    } finally {
      setLoading(false);
    }
  };

  // 보안 분석 정보 조회
  const fetchSecurityAnalytics = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/files/security-analytics`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setSecurityAnalytics(data);
      } else {
        console.error('보안 분석 정보 조회 실패');
      }
    } catch (err) {
      console.error('보안 분석 정보 조회 오류:', err);
    }
  };

  useEffect(() => {
    fetchAccessLogs();
    fetchSecurityAnalytics();
  }, []);

  const getActionBadgeColor = (action) => {
    if (action.includes('success')) return 'bg-green-100 text-green-800';
    if (action.includes('denied') || action.includes('blocked')) return 'bg-red-100 text-red-800';
    if (action.includes('failed') || action.includes('error')) return 'bg-yellow-100 text-yellow-800';
    return 'bg-blue-100 text-blue-800';
  };

  const getActionText = (action) => {
    const actionMap = {
      'download_success': '다운로드 성공',
      'download_denied': '다운로드 거부',
      'download_failed': '다운로드 실패',
      'download_blocked': '다운로드 차단',
      'download_error': '다운로드 오류',
      'preview_success': '미리보기 성공',
      'preview_denied': '미리보기 거부',
      'preview_failed': '미리보기 실패',
      'preview_blocked': '미리보기 차단',
      'preview_error': '미리보기 오류',
      'metadata_access': '메타데이터 접근'
    };
    return actionMap[action] || action;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600 font-medium">보안 정보 로딩 중...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-6">파일 보안 대시보드</h2>

        {/* 보안 분석 요약 */}
        {securityAnalytics && (
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-3">보안 현황 ({securityAnalytics.period})</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-medium text-blue-800">총 접근 시도</h4>
                <p className="text-2xl font-bold text-blue-600">
                  {securityAnalytics.action_statistics.reduce((sum, stat) => sum + stat.count, 0)}
                </p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-medium text-green-800">성공한 접근</h4>
                <p className="text-2xl font-bold text-green-600">
                  {securityAnalytics.action_statistics.reduce((sum, stat) => sum + stat.success_count, 0)}
                </p>
              </div>
              <div className="bg-red-50 p-4 rounded-lg">
                <h4 className="font-medium text-red-800">차단된 접근</h4>
                <p className="text-2xl font-bold text-red-600">
                  {securityAnalytics.action_statistics.reduce((sum, stat) => sum + stat.failure_count, 0)}
                </p>
              </div>
            </div>

            {/* 의심 활동 알림 */}
            {securityAnalytics.suspicious_activities.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <h4 className="font-medium text-red-800 mb-2">⚠️ 의심스러운 활동 감지</h4>
                <div className="space-y-2">
                  {securityAnalytics.suspicious_activities.map((activity, index) => (
                    <div key={index} className="text-sm text-red-700">
                      사용자 <strong>{activity.user_name}</strong>: {activity.failed_attempts}회 실패
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 보안 권장사항 */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h4 className="font-medium text-yellow-800 mb-2">💡 보안 권장사항</h4>
              <ul className="text-sm text-yellow-700 space-y-1">
                {securityAnalytics.security_recommendations.map((recommendation, index) => (
                  <li key={index}>• {recommendation}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* 필터링 섹션 */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-medium mb-3">접근 로그 필터</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">파일 ID</label>
              <input
                type="text"
                value={filters.file_id}
                onChange={(e) => setFilters(prev => ({ ...prev, file_id: e.target.value }))}
                placeholder="파일 ID"
                className="w-full p-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">사용자 ID</label>
              <input
                type="text"
                value={filters.user_id}
                onChange={(e) => setFilters(prev => ({ ...prev, user_id: e.target.value }))}
                placeholder="사용자 ID"
                className="w-full p-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">액션</label>
              <select
                value={filters.action}
                onChange={(e) => setFilters(prev => ({ ...prev, action: e.target.value }))}
                className="w-full p-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="">전체</option>
                <option value="download_success">다운로드 성공</option>
                <option value="download_denied">다운로드 거부</option>
                <option value="preview_success">미리보기 성공</option>
                <option value="preview_denied">미리보기 거부</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">시작 날짜</label>
              <input
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilters(prev => ({ ...prev, start_date: e.target.value }))}
                className="w-full p-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">종료 날짜</label>
              <input
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilters(prev => ({ ...prev, end_date: e.target.value }))}
                className="w-full p-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
          </div>
          <div className="mt-4 flex space-x-3">
            <button
              onClick={fetchAccessLogs}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              필터 적용
            </button>
            <button
              onClick={() => {
                setFilters({ file_id: '', user_id: '', action: '', start_date: '', end_date: '', limit: 100 });
                setTimeout(fetchAccessLogs, 100);
              }}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              초기화
            </button>
          </div>
        </div>

        {/* 에러 표시 */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-3 flex-1">
                <h3 className="text-sm font-medium text-red-800">오류가 발생했습니다</h3>
                <p className="mt-1 text-sm text-red-700">{error}</p>
                <div className="mt-3">
                  <button
                    onClick={() => {
                      setError(null);
                      fetchAccessLogs();
                    }}
                    className="text-sm bg-red-100 text-red-800 px-3 py-1 rounded-md hover:bg-red-200 transition-colors"
                  >
                    다시 시도
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 접근 로그 테이블 */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">시간</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">사용자</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">파일</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">액션</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP 주소</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">결과</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">오류 메시지</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {accessLogs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                    조회된 로그가 없습니다.
                  </td>
                </tr>
              ) : (
                accessLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.access_time_formatted}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.user_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="max-w-48 truncate" title={log.file_name}>
                        {log.file_name}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getActionBadgeColor(log.action)}`}>
                        {getActionText(log.action)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.ip_address}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        log.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {log.success ? '성공' : '실패'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="max-w-48 truncate" title={log.error_message}>
                        {log.error_message || '-'}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* 로그 수 정보 */}
        <div className="mt-4 text-sm text-gray-600">
          총 {accessLogs.length}개의 로그가 조회되었습니다.
        </div>
      </div>
    </div>
  );
};

export default FileSecurityDashboard;