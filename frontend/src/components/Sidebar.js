import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  FaUser,
  FaCog,
  FaChartBar,
  FaHome,
  FaSignOutAlt,
  FaBuilding,
  FaRegClipboard,
  FaLock,
  FaHistory,
  FaUsersCog,
  FaFlag,
  FaClipboardList,
  FaSearch,
  FaStore,
  FaTasks,
  FaRegChartBar,
  FaWarehouse,
  FaCaretDown,
  FaFileAlt,
} from 'react-icons/fa';
import './Sidebar.css';

function Sidebar({ handleLogout }) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [systemAuditsOpen, setSystemAuditsOpen] = useState(false);
  const [manageItemsOpen, setManageItemsOpen] = useState(false);
  const [salesOpen, setSalesOpen] = useState(false);

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <img src="#" alt="App Logo" /> {/* Replace with your logo path */}
      </div>
      <div className="sidebar-menu">
        <ul>
          <li>
            <NavLink
              to="/dashboard"
              className={({ isActive }) => (isActive ? 'active' : '')}
            >
              <FaHome />
              <span>Dashboard</span>
            </NavLink>
          </li>

          {/* Sales Dropdown */}
          <li>
            <div onClick={() => setSalesOpen(!salesOpen)} className="sidebar-dropdown">
              <FaChartBar />
              <span>Sales</span>
              <FaCaretDown />
            </div>
            {salesOpen && (
              <ul className="submenu">
                <li>
                  <NavLink
                    to="/sales"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaChartBar />
                    <span>Sales</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/incepted-sales"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaClipboardList />
                    <span>Incepted Sales</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/sales-performance"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaRegChartBar />
                    <span>Sales Performance</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/flagged-investigations"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaFlag />
                    <span>Flagged Investigations</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/queries"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaSearch />
                    <span>Queries</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/reports"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaFileAlt />
                    <span>Reports</span>
                  </NavLink>
                </li>
              </ul>
            )}
          </li>

          {/* Manage Items Dropdown */}
          <li>
            <div onClick={() => setManageItemsOpen(!manageItemsOpen)} className="sidebar-dropdown">
              <FaTasks />
              <span>Manage Items</span>
              <FaCaretDown />
            </div>
            {manageItemsOpen && (
              <ul className="submenu">
                <li>
                  <NavLink
                    to="/manage-banks"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaBuilding />
                    <span>Bank Management</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/branches"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaWarehouse />
                    <span>Branch Management</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/sales-executive-management"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaTasks />
                    <span>Sales Executive Management</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/paypoints"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaStore />
                    <span>Paypoint Management</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/products"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaRegClipboard />
                    <span>Products Management</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/manage-users"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaUser />
                    <span>User Management</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/sales-target-management"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaChartBar />
                    <span>Sales Target Management</span>
                  </NavLink>
                </li>
              </ul>
            )}
          </li>

          {/* System Audits Dropdown */}
          <li>
            <div onClick={() => setSystemAuditsOpen(!systemAuditsOpen)} className="sidebar-dropdown">
              <FaRegChartBar />
              <span>System Audits</span>
              <FaCaretDown />
            </div>
            {systemAuditsOpen && (
              <ul className="submenu">
                <li>
                  <NavLink
                    to="/audit-trail"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaRegChartBar />
                    <span>Audit Trail</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/logs"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaClipboardList />
                    <span>Logs</span>
                  </NavLink>
                </li>
              </ul>
            )}
          </li>

          {/* Settings Dropdown */}
          <li>
            <div onClick={() => setSettingsOpen(!settingsOpen)} className="sidebar-dropdown">
              <FaCog />
              <span>Settings</span>
              <FaCaretDown />
            </div>
            {settingsOpen && (
              <ul className="submenu">
                <li>
                  <NavLink
                    to="/user-sessions"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaHistory />
                    <span>User Sessions</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/manage-roles"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaUsersCog />
                    <span>Role Management</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/manage-access"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaLock />
                    <span>Access Management</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/retention-policy"
                    className={({ isActive }) => (isActive ? 'active' : '')}
                  >
                    <FaHistory />
                    <span>Retention Policy</span>
                  </NavLink>
                </li>
              </ul>
            )}
          </li>
        </ul>
      </div>
      <div className="sidebar-footer">
        <button onClick={handleLogout}>
          <FaSignOutAlt />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
}

export default Sidebar;
