import { useState } from 'react';
import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
}) {
  // 현재 열린 메뉴의 대화 ID
  const [openMenuId, setOpenMenuId] = useState(null);
  // 삭제 확인 모달에 표시할 대화 ID
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);

  // 메뉴 버튼 클릭 핸들러
  const handleMenuClick = (e, convId) => {
    e.stopPropagation();
    setOpenMenuId(openMenuId === convId ? null : convId);
  };

  // 삭제 버튼 클릭 핸들러
  const handleDeleteClick = (e, convId) => {
    e.stopPropagation();
    setOpenMenuId(null);
    setDeleteConfirmId(convId);
  };

  // 삭제 확인 핸들러
  const handleConfirmDelete = () => {
    if (deleteConfirmId) {
      onDeleteConversation(deleteConfirmId);
      setDeleteConfirmId(null);
    }
  };

  // 삭제 취소 핸들러
  const handleCancelDelete = () => {
    setDeleteConfirmId(null);
  };

  // 외부 클릭 시 메뉴 닫기
  const handleConversationClick = (convId) => {
    setOpenMenuId(null);
    onSelectConversation(convId);
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>LLM Council</h1>
        <button className="new-conversation-btn" onClick={onNewConversation}>
          + New Conversation
        </button>
      </div>

      <div className="conversation-list">
        {conversations.length === 0 ? (
          <div className="no-conversations">No conversations yet</div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${
                conv.id === currentConversationId ? 'active' : ''
              }`}
              onClick={() => handleConversationClick(conv.id)}
            >
              <div className="conversation-content">
                <div className="conversation-title">
                  {conv.title || 'New Conversation'}
                </div>
                <div className="conversation-meta">
                  {conv.message_count} messages
                </div>
              </div>

              {/* 메뉴 버튼 (⋮) */}
              <button
                className="menu-button"
                onClick={(e) => handleMenuClick(e, conv.id)}
              >
                ⋮
              </button>

              {/* 드롭다운 메뉴 */}
              {openMenuId === conv.id && (
                <div className="dropdown-menu">
                  <button
                    className="dropdown-item delete"
                    onClick={(e) => handleDeleteClick(e, conv.id)}
                  >
                    Delete
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* 삭제 확인 모달 */}
      {deleteConfirmId && (
        <div className="modal-overlay" onClick={handleCancelDelete}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Delete Conversation</h3>
            <p>Are you sure you want to delete this conversation?</p>
            <div className="modal-buttons">
              <button className="cancel-btn" onClick={handleCancelDelete}>
                Cancel
              </button>
              <button className="delete-btn" onClick={handleConfirmDelete}>
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
