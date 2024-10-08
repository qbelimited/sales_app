import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  FaChartBar,
  FaHome,
  FaBuilding,
  FaFlag,
  FaClipboardList,
  FaSearch,
  FaStore,
  FaTasks,
  FaRegChartBar,
  FaWarehouse,
  FaCaretDown,
  FaFileAlt,
  FaLock,
  FaHistory,
  FaUser,
  FaCog,
  FaFolder,
  FaUsers,
  FaBullseye,
  FaFileContract,
  FaQuestionCircle,
} from 'react-icons/fa';
import './Sidebar.css';

function Sidebar() {
  const [openDropdown, setOpenDropdown] = useState(null);
  const location = useLocation();

  const local_user = JSON.parse(localStorage.getItem('user')) || {};
  const role_id = parseInt(local_user?.role_id) || local_user?.role?.id || 0;

  const handleDropdownClick = (dropdown) => {
    setOpenDropdown((prev) => (prev === dropdown ? null : dropdown));
  };

  const handleKeyDown = (event, dropdown) => {
    if (event.key === 'Enter' || event.key === ' ') {
      handleDropdownClick(dropdown);
    } else if (event.key === 'Escape' && openDropdown === dropdown) {
      setOpenDropdown(null);
    }
  };

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path);

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>S-T</h1>
      </div>
      <div className="sidebar-menu">
        <ul>
          <li>
            <NavLink to="/dashboard" className={({ isActive }) => (isActive ? 'active' : '')}>
              <FaHome />
              <span>Dashboard</span>
            </NavLink>
          </li>
          <li>
            <button
              aria-expanded={openDropdown === 'sales'}
              onClick={() => handleDropdownClick('sales')}
              onKeyDown={(event) => handleKeyDown(event, 'sales')}
              className={`sidebar-dropdown ${openDropdown === 'sales' || isActive('/sales') ? 'active' : ''}`}
            >
              <FaChartBar />
              <span>Manage Sales</span>
              <FaCaretDown className={`caret ${openDropdown === 'sales' ? 'rotate' : ''}`} />
            </button>
            {openDropdown === 'sales' && (
              <ul className="submenu">
                <li>
                  <NavLink to="/sales" className={({ isActive }) => (isActive ? 'active' : '')}>
                    <FaChartBar />
                    <span>Make/View Sales</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink to="/incepted-sales" className={({ isActive }) => (isActive ? 'active' : '')}>
                    <FaClipboardList />
                    <span>Incepted Sales</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink to="/sales-performance" className={({ isActive }) => (isActive ? 'active' : '')}>
                    <FaRegChartBar />
                    <span>Sales Performance</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink to="/sales-targets" className={({ isActive }) => (isActive ? 'active' : '')}>
                    <FaBullseye />
                    <span>Sales Targets</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink to="/investigations" className={({ isActive }) => (isActive ? 'active' : '')}>
                    <FaFlag />
                    <span>Flagged Investigations</span>
                  </NavLink>
                </li>
              </ul>
            )}
          </li>
          <li>
            <button
              aria-expanded={openDropdown === 'manageItems'}
              onClick={() => handleDropdownClick('manageItems')}
              onKeyDown={(event) => handleKeyDown(event, 'manageItems')}
              className={`sidebar-dropdown ${openDropdown === 'manageItems' || isActive('/manage-sales-executives') || isActive('/manage-banks') || isActive('/manage-paypoints') || isActive('/manage-products') || isActive('/manage-branches') ? 'active' : ''}`}
            >
              <FaTasks />
              <span>Manage Items</span>
              <FaCaretDown className={`caret ${openDropdown === 'manageItems' ? 'rotate' : ''}`} />
            </button>
            {openDropdown === 'manageItems' && (
              <ul className="submenu">
                <li>
                  <NavLink to="/manage-sales-executives" className={({ isActive }) => (isActive ? 'active' : '')}>
                    <FaUsers />
                    <span>Manage SEs</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink to="/manage-banks" className={({ isActive }) => (isActive ? 'active' : '')}>
                    <FaBuilding />
                    <span>Manage Banks</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink to="/manage-paypoints" className={({ isActive }) => (isActive ? 'active' : '')}>
                    <FaSearch />
                    <span>Manage Paypoints</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink to="/manage-products" className={({ isActive }) => (isActive ? 'active' : '')}>
                    <FaStore />
                    <span>Manage Products</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink to="/manage-branches" className={({ isActive }) => (isActive ? 'active' : '')}>
                    <FaWarehouse />
                    <span>Manage Branches</span>
                  </NavLink>
                </li>
              </ul>
            )}
          </li>
          {(role_id === 1 || role_id === 2 || role_id === 3) && (
          <li>
            <NavLink to="/reports" className={({ isActive }) => (isActive ? 'active' : '')}>
              <FaFileContract />
              <span>Reports</span>
            </NavLink>
          </li>
          )}
          <li>
            <NavLink to="/help-center" className={({ isActive }) => (isActive ? 'active' : '')}>
              <FaQuestionCircle />
              <span>Help Center</span>
            </NavLink>
          </li>
          {(role_id === 1 || role_id === 2 || role_id === 3) && (
            <li>
              <button
                aria-expanded={openDropdown === 'settings'}
                onClick={() => handleDropdownClick('settings')}
                onKeyDown={(event) => handleKeyDown(event, 'settings')}
                className={`sidebar-dropdown ${openDropdown === 'settings' || isActive('/manage-users') || isActive('/manage-users-sessions') || isActive('/manage-roles') ? 'active' : ''}`}
              >
                <FaCog />
                <span>Settings</span>
                <FaCaretDown className={`caret ${openDropdown === 'settings' ? 'rotate' : ''}`} />
              </button>
              {openDropdown === 'settings' && (
                <ul className="submenu">
                  <li>
                    <NavLink to="/manage-users" className={({ isActive }) => (isActive ? 'active' : '')}>
                      <FaUsers />
                      <span>Manage Users</span>
                    </NavLink>
                  </li>
                  <li>
                    <NavLink to="/manage-users-sessions" className={({ isActive }) => (isActive ? 'active' : '')}>
                      <FaUser />
                      <span>Manage Users Sessions</span>
                    </NavLink>
                  </li>
                  <li>
                    <NavLink to="/manage-roles" className={({ isActive }) => (isActive ? 'active' : '')}>
                      <FaLock />
                      <span>Manage Roles & Permissions</span>
                    </NavLink>
                  </li>
                </ul>
              )}
            </li>
          )}
          {role_id === 3 && (
            <li>
              <button
                aria-expanded={openDropdown === 'systemAudits'}
                onClick={() => handleDropdownClick('systemAudits')}
                onKeyDown={(event) => handleKeyDown(event, 'systemAudits')}
                className={`sidebar-dropdown ${openDropdown === 'systemAudits' || isActive('/audit-trail') || isActive('/logs') || isActive('/retention-policy') ? 'active' : ''}`}
              >
                <FaHistory />
                <span>System Audits</span>
                <FaCaretDown className={`caret ${openDropdown === 'systemAudits' ? 'rotate' : ''}`} />
              </button>
              {openDropdown === 'systemAudits' && (
                <ul className="submenu">
                  <li>
                    <NavLink to="/audit-trail" className={({ isActive }) => (isActive ? 'active' : '')}>
                      <FaHistory />
                      <span>Audit Trail</span>
                    </NavLink>
                  </li>
                  <li>
                    <NavLink to="/logs" className={({ isActive }) => (isActive ? 'active' : '')}>
                      <FaFileAlt />
                      <span>Logs</span>
                    </NavLink>
                  </li>
                  <li>
                    <NavLink to="/retention-policy" className={({ isActive }) => (isActive ? 'active' : '')}>
                      <FaFolder />
                      <span>Retention Policy</span>
                    </NavLink>
                  </li>
                </ul>
              )}
            </li>
          )}
        </ul>
      </div>
    </div>
  );
}

export default Sidebar;
