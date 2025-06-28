import React, { useState, useEffect } from 'react';

/**
 * 📊 Enhanced Navigation System - Design Proposal
 * 
 * Current Issues Identified:
 * 1. Tab-based navigation without URL routing
 * 2. Heavy admin dropdown menu causing UX confusion
 * 3. No breadcrumbs or navigation context
 * 4. Limited mobile responsiveness in navigation
 * 5. No keyboard navigation support
 * 
 * Proposed Solutions:
 * 1. Implement React Router for URL-based navigation
 * 2. Restructure admin menu into sidebar panel
 * 3. Add breadcrumb navigation
 * 4. Improve mobile navigation with collapsible menu
 * 5. Add ARIA labels and keyboard navigation
 */

// 🎯 Navigation Structure Redesign
const NAVIGATION_STRUCTURE = {
  primary: [
    {
      id: 'dashboard',
      label: '📊 대시보드',
      path: '/dashboard',
      roles: ['admin', 'secretary'],
      description: '시스템 전체 현황과 주요 지표를 확인합니다.'
    },
    {
      id: 'projects',
      label: '🎯 프로젝트',
      path: '/projects',
      roles: ['admin', 'secretary'],
      description: '평가 프로젝트를 생성하고 관리합니다.'
    },
    {
      id: 'evaluations',
      label: '📝 평가',
      path: '/evaluations',
      roles: ['admin', 'secretary', 'evaluator'],
      description: '평가 진행 현황과 결과를 관리합니다.'
    },
    {
      id: 'templates',
      label: '📄 템플릿',
      path: '/templates',
      roles: ['admin', 'secretary'],
      description: '평가 템플릿을 생성하고 수정합니다.'
    }
  ],
  tools: [
    {
      id: 'file-viewer',
      label: '🔒 파일 뷰어',
      path: '/files',
      roles: ['admin', 'secretary', 'evaluator'],
      description: '보안이 적용된 파일을 안전하게 열람합니다.'
    },
    {
      id: 'print-manager',
      label: '🖨️ 출력 관리',
      path: '/print',
      roles: ['admin', 'secretary', 'evaluator'],
      description: '평가표와 보고서를 출력하고 내보냅니다.'
    },
    {
      id: 'ai-assistant',
      label: '🤖 AI 도우미',
      path: '/ai',
      roles: ['admin', 'secretary', 'evaluator'],
      description: 'AI 기반 문서 분석과 평가 지원을 받습니다.'
    },
    {
      id: 'analytics',
      label: '📈 분석',
      path: '/analytics',
      roles: ['admin', 'secretary'],
      description: '평가 결과를 분석하고 리포트를 생성합니다.'
    }
  ],
  admin: [
    {
      id: 'users',
      label: '👥 사용자 관리',
      path: '/admin/users',
      roles: ['admin'],
      description: '시스템 사용자를 관리하고 권한을 설정합니다.'
    },
    {
      id: 'ai-models',
      label: '🔧 AI 모델',
      path: '/admin/ai-models',
      roles: ['admin'],
      description: 'AI 모델을 설정하고 성능을 모니터링합니다.'
    },
    {
      id: 'ai-providers',
      label: '🌐 AI 공급자',
      path: '/admin/ai-providers',
      roles: ['admin'],
      description: 'AI 서비스 공급자를 관리합니다.'
    },
    {
      id: 'security',
      label: '🛡️ 보안',
      path: '/admin/security',
      roles: ['admin'],
      description: '파일 보안과 접근 권한을 관리합니다.'
    },
    {
      id: 'deployment',
      label: '🚀 배포',
      path: '/admin/deployment',
      roles: ['admin'],
      description: '시스템 배포와 환경을 관리합니다.'
    }
  ]
};

// 🎨 Enhanced Navigation Component
const EnhancedNavigation = ({ user, activeTab, setActiveTab }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isAdminPanelOpen, setIsAdminPanelOpen] = useState(false);
  const [hoveredItem, setHoveredItem] = useState(null);

  // Filter navigation items based on user role
  const getFilteredItems = (items) => {
    return items.filter(item => item.roles.includes(user.role));
  };

  // Generate breadcrumb trail
  const getBreadcrumbs = () => {
    const allItems = [...NAVIGATION_STRUCTURE.primary, ...NAVIGATION_STRUCTURE.tools, ...NAVIGATION_STRUCTURE.admin];
    const currentItem = allItems.find(item => item.id === activeTab);
    
    const breadcrumbs = [
      { label: '홈', path: '/' }
    ];
    
    if (currentItem) {
      if (NAVIGATION_STRUCTURE.admin.includes(currentItem)) {
        breadcrumbs.push({ label: '관리자', path: '/admin' });
      }
      breadcrumbs.push({ label: currentItem.label, path: currentItem.path });
    }
    
    return breadcrumbs;
  };

  return (
    <div className="enhanced-navigation">
      {/* 🍞 Breadcrumb Navigation */}
      <div className="bg-gray-50 border-b border-gray-200 px-6 py-2">
        <nav className="flex" aria-label="Breadcrumb">
          <ol className="flex items-center space-x-2 text-sm">
            {getBreadcrumbs().map((crumb, index) => (
              <li key={index} className="flex items-center">
                {index > 0 && <span className="text-gray-400 mx-2">/</span>}
                <span className={`${
                  index === getBreadcrumbs().length - 1 
                    ? 'text-gray-900 font-medium' 
                    : 'text-gray-500 hover:text-gray-700'
                }`}>
                  {crumb.label}
                </span>
              </li>
            ))}
          </ol>
        </nav>
      </div>

      {/* 📱 Mobile Menu Button */}
      <div className="lg:hidden bg-white border-b border-gray-200 px-4 py-3">
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="flex items-center justify-center w-8 h-8 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100"
          aria-label="메뉴 열기"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>

      {/* 🖥️ Desktop Navigation */}
      <nav className={`bg-white border-b border-gray-200 ${isMobileMenuOpen ? 'block' : 'hidden lg:block'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          {/* Primary Navigation */}
          <div className="flex space-x-8 overflow-x-auto">
            {getFilteredItems(NAVIGATION_STRUCTURE.primary).map(item => (
              <NavigationItem
                key={item.id}
                item={item}
                isActive={activeTab === item.id}
                onClick={() => setActiveTab(item.id)}
                onHover={setHoveredItem}
                isHovered={hoveredItem === item.id}
              />
            ))}
            
            {/* Tools Dropdown */}
            <DropdownMenu
              label="🔧 도구"
              items={getFilteredItems(NAVIGATION_STRUCTURE.tools)}
              activeTab={activeTab}
              setActiveTab={setActiveTab}
            />
            
            {/* Admin Panel for Admins */}
            {user.role === 'admin' && (
              <>
                <button
                  onClick={() => setIsAdminPanelOpen(true)}
                  className="py-4 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 font-medium text-sm transition-colors"
                >
                  ⚙️ 관리자
                </button>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* 🎛️ Admin Side Panel */}
      {isAdminPanelOpen && (
        <AdminSidePanel
          items={getFilteredItems(NAVIGATION_STRUCTURE.admin)}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onClose={() => setIsAdminPanelOpen(false)}
        />
      )}

      {/* 💡 Tooltip for Hovered Items */}
      {hoveredItem && (
        <NavigationTooltip
          item={[...NAVIGATION_STRUCTURE.primary, ...NAVIGATION_STRUCTURE.tools, ...NAVIGATION_STRUCTURE.admin]
            .find(item => item.id === hoveredItem)}
        />
      )}
    </div>
  );
};

// 🎯 Individual Navigation Item Component
const NavigationItem = ({ item, isActive, onClick, onHover, isHovered }) => (
  <button
    onClick={onClick}
    onMouseEnter={() => onHover(item.id)}
    onMouseLeave={() => onHover(null)}
    className={`py-4 px-1 border-b-2 font-medium text-sm transition-all duration-200 ${
      isActive
        ? 'border-blue-500 text-blue-600'
        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
    } ${isHovered ? 'transform scale-105' : ''}`}
    aria-label={`${item.label} 페이지로 이동`}
    aria-current={isActive ? 'page' : undefined}
  >
    {item.label}
  </button>
);

// 📋 Dropdown Menu Component
const DropdownMenu = ({ label, items, activeTab, setActiveTab }) => {
  const [isOpen, setIsOpen] = useState(false);
  const hasActiveItem = items.some(item => item.id === activeTab);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center space-x-1 ${
          hasActiveItem
            ? 'border-blue-500 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
        }`}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <span>{label}</span>
        <svg className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          <div className="py-2">
            {items.map(item => (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setIsOpen(false);
                }}
                className={`w-full text-left px-4 py-3 text-sm hover:bg-gray-50 transition-colors ${
                  activeTab === item.id ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
                }`}
              >
                <div className="font-medium">{item.label}</div>
                <div className="text-xs text-gray-500 mt-1">{item.description}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// 🎛️ Admin Side Panel Component
const AdminSidePanel = ({ items, activeTab, setActiveTab, onClose }) => (
  <div className="fixed inset-0 z-50 overflow-hidden">
    {/* Backdrop */}
    <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose}></div>
    
    {/* Panel */}
    <div className="absolute right-0 top-0 h-full w-80 bg-white shadow-xl">
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">⚙️ 관리자 도구</h2>
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-100 rounded-md"
          aria-label="관리자 패널 닫기"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div className="p-4 space-y-2">
        {items.map(item => (
          <button
            key={item.id}
            onClick={() => {
              setActiveTab(item.id);
              onClose();
            }}
            className={`w-full text-left p-3 rounded-lg transition-colors ${
              activeTab === item.id 
                ? 'bg-blue-50 text-blue-600 border border-blue-200' 
                : 'hover:bg-gray-50 text-gray-700'
            }`}
          >
            <div className="font-medium">{item.label}</div>
            <div className="text-xs text-gray-500 mt-1">{item.description}</div>
          </button>
        ))}
      </div>
    </div>
  </div>
);

// 💡 Navigation Tooltip Component
const NavigationTooltip = ({ item }) => (
  <div className="fixed z-50 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg shadow-lg pointer-events-none">
    <div className="font-medium">{item.label}</div>
    <div className="text-gray-300 text-xs mt-1">{item.description}</div>
  </div>
);

export default EnhancedNavigation;
export { NAVIGATION_STRUCTURE };