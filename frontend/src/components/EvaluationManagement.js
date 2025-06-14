import React, { useEffect, useState } from "react";
import CreateEvaluationPage from "./CreateEvaluationPage.js";

const EvaluationManagement = ({ user }) => {
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedEvaluation, setSelectedEvaluation] = useState(null);
  const [currentView, setCurrentView] = useState('list'); // 'list' or 'create'

  useEffect(() => {
    fetchEvaluations();
  }, []);
  const fetchEvaluations = async () => {
    setLoading(true);
    setError("");
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080'}/api/evaluations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: '평가 목록을 불러오는데 실패했습니다.' }));
        throw new Error(errData.detail || '평가 목록을 불러오는데 실패했습니다.');
      }
      const data = await response.json();
      setEvaluations(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluationCreated = () => {
    setCurrentView('list');
    fetchEvaluations(); // Refresh the list
  };

  if (user.role !== 'admin' && user.role !== 'secretary') {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">평가 관리</h2>
        <p className="text-gray-600">이 기능은 관리자와 간사만 사용할 수 있습니다.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600 font-medium">평가 목록 로딩 중...</span>
      </div>
    );
  }
  if (error) {
    return <div className="text-red-500 p-4 bg-red-100 border border-red-400 rounded">오류: {error}</div>;
  }

  // Show CreateEvaluationPage when currentView is 'create'
  if (currentView === 'create') {
    return (
      <CreateEvaluationPage 
        user={user}
        onEvaluationCreated={handleEvaluationCreated}
        onCancel={() => setCurrentView('list')}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">평가 관리</h2>
          <button
            onClick={() => setCurrentView('create')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            + 새 평가 개설
          </button>
        </div>
        {evaluations.length === 0 ? (
          <p className="text-gray-500 text-center py-8">등록된 평가가 없습니다.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">평가 ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">프로젝트명</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">평가자</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">피평가자</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">평가일</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">작업</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {evaluations.map((evalItem) => (
                  <tr key={evalItem.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{evalItem.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{evalItem.project_name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{evalItem.evaluator_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{evalItem.evaluatee_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${evalItem.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>{evalItem.status}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{evalItem.evaluation_date ? new Date(evalItem.evaluation_date).toLocaleDateString() : '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => setSelectedEvaluation(evalItem)}
                        className="text-indigo-600 hover:text-indigo-900 px-3 py-1 rounded-md hover:bg-indigo-50 transition-colors"
                      >
                        상세
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {/* 평가 상세 모달 */}
      {selectedEvaluation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg mx-4">
            <h3 className="text-lg font-semibold mb-4">평가 상세</h3>
            <div className="space-y-2">
              <div><b>평가 ID:</b> {selectedEvaluation.id}</div>
              <div><b>프로젝트명:</b> {selectedEvaluation.project_name}</div>
              <div><b>평가자:</b> {selectedEvaluation.evaluator_id}</div>
              <div><b>피평가자:</b> {selectedEvaluation.evaluatee_id}</div>
              <div><b>상태:</b> {selectedEvaluation.status}</div>
              <div><b>평가일:</b> {selectedEvaluation.evaluation_date ? new Date(selectedEvaluation.evaluation_date).toLocaleDateString() : '-'}</div>
              <div><b>점수/의견:</b> <pre className="bg-gray-50 p-2 rounded text-xs overflow-x-auto">{JSON.stringify(selectedEvaluation.scores, null, 2)}</pre></div>
              <div><b>종합 의견:</b> <div className="bg-gray-50 p-2 rounded text-xs">{selectedEvaluation.comments}</div></div>
            </div>
            <div className="flex justify-end space-x-3 pt-6">
              <button
                type="button"
                onClick={() => setSelectedEvaluation(null)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EvaluationManagement;
