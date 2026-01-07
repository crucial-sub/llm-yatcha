import { useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
}) {
  const { theme, toggleTheme } = useTheme();
  // Currently open menu's conversation ID
  const [openMenuId, setOpenMenuId] = useState(null);
  // Conversation ID to show in delete confirmation modal
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);

  // Menu button click handler
  const handleMenuClick = (e, convId) => {
    e.stopPropagation();
    setOpenMenuId(openMenuId === convId ? null : convId);
  };

  // Delete button click handler
  const handleDeleteClick = (e, convId) => {
    e.stopPropagation();
    setOpenMenuId(null);
    setDeleteConfirmId(convId);
  };

  // Confirm delete handler
  const handleConfirmDelete = () => {
    if (deleteConfirmId) {
      onDeleteConversation(deleteConfirmId);
      setDeleteConfirmId(null);
    }
  };

  // Cancel delete handler
  const handleCancelDelete = () => {
    setDeleteConfirmId(null);
  };

  // Close menu on outside click
  const handleConversationClick = (convId) => {
    setOpenMenuId(null);
    onSelectConversation(convId);
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title-row">
          <h1>LLM Council</h1>
          <button
            className="theme-toggle-btn"
            onClick={toggleTheme}
            title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>
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

              {/* Menu button (⋮) */}
              <button
                className="menu-button"
                onClick={(e) => handleMenuClick(e, conv.id)}
              >
                ⋮
              </button>

              {/* Dropdown menu */}
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

      {/* Delete confirmation modal */}
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
