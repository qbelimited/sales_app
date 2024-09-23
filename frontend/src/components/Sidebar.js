import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
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
  FaCaretDown,
  FaFileAlt,
  FaLock,
  FaHistory,
  FaUser,
  FaCog,
  FaFolder,
  FaBars,  // Hamburger Icon for Mobile
} from 'react-icons/fa';
import './Sidebar.css'; // CSS for sidebar responsiveness

function Sidebar({ userRole, isSidebarOpen, toggleSidebar }) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [systemAuditsOpen, setSystemAuditsOpen] = useState(false);
  const [manageItemsOpen, setManageItemsOpen] = useState(false);
  const [salesOpen, setSalesOpen] = useState(false);

  // Handle dropdown toggles
  const handleSettingsClick = () => setSettingsOpen(!settingsOpen);
  const handleSystemAuditsClick = () => setSystemAuditsOpen(!systemAuditsOpen);
  const handleManageItemsClick = () => setManageItemsOpen(!manageItemsOpen);
  const handleSalesClick = () => setSalesOpen(!salesOpen);

  const isAllowed = (allowedRoles) => allowedRoles.includes(userRole);

  return (
    <div className={`sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
      {/* Mobile Header with Hamburger Icon */}
      <div className="mobile-header">
        <FaBars className="hamburger-icon" onClick={toggleSidebar} />
      </div>

      {/* Sidebar Menu */}
      <div className="sidebar-content">
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

            {/* Sales Dropdown */}
            {isAllowed([1, 2, 3, 4]) && (
              <li>
                <div onClick={handleSalesClick} className="sidebar-dropdown">
                  <FaChartBar />
                  <span>Manage Sales</span>
                  <FaCaretDown />
                </div>
                {salesOpen && (
                  <ul className="submenu">
                    {isAllowed([1, 2, 3, 4]) && (
                      <li>
                        <NavLink to="/sales" className={({ isActive }) => (isActive ? 'active' : '')}>
                          <FaChartBar />
                          <span>Make/View Sales</span>
                        </NavLink>
                      </li>
                    )}
                    {isAllowed([1, 2, 3, 4]) && (
                      <li>
                        <NavLink to="/incepted-sales" className={({ isActive }) => (isActive ? 'active' : '')}>
                          <FaClipboardList />
                          <span>Incepted Sales</span>
                        </NavLink>
                      </li>
                    )}
                    {isAllowed([1, 2, 3, 4]) && (
                      <li>
                        <NavLink to="/sales-performance" className={({ isActive }) => (isActive ? 'active' : '')}>
                          <FaRegChartBar />
                          <span>Sales Performance</span>
                        </NavLink>
                      </li>
                    )}
                    {isAllowed([1, 2, 3]) && (
                      <li>
                        <NavLink to="/flagged-investigations" className={({ isActive }) => (isActive ? 'active' : '')}>
                          <FaFlag />
                          <span>Flagged Investigations</span>
                        </NavLink>
                      </li>
                    )}
                  </ul>
                )}
              </li>
            )}

            {/* Manage Items Dropdown */}
            {isAllowed([1, 2, 3]) && (
              <li>
                <div onClick={handleManageItemsClick} className="sidebar-dropdown">
                  <FaTasks />
                  <span> Manage Items</span>
                  <FaCaretDown />
                </div>
                {manageItemsOpen && (
                  <ul className="submenu">
                    {isAllowed([1, 2, 3]) && (
                      <li>
                        <NavLink to="/manage-banks" className={({ isActive }) => (isActive ? 'active' : '')}>
                          <FaBuilding />
                          <span>Manage Banks</span>
                        </NavLink>
                      </li>
                    )}
                    {isAllowed([1, 2, 3]) && (
                      <li>
                        <NavLink to="/manage-products" className={({ isActive }) => (isActive ? 'active' : '')}>
                          <FaStore />
                          <span>Manage Products</span>
                        </NavLink>
                      </li>
                    )}
                    {isAllowed([1, 2, 3]) && (
                      <li>
                        <NavLink to="/manage-paypoints" className={({ isActive }) => (isActive ? 'active' : '')}>
                          <FaSearch />
                          <span>Manage Paypoints</span>
                        </NavLink>
                      </li>
                    )}
                  </ul>
                )}
              </li>
            )}

            {/* Settings Dropdown */}
            {isAllowed([2, 3]) && (
              <li>
                <div onClick={handleSettingsClick} className="sidebar-dropdown">
                  <FaCog />
                  <span> Settings</span>
                  <FaCaretDown />
                </div>
                {settingsOpen && (
                  <ul className="submenu">
                    {isAllowed([2, 3]) && (
                      <li>
                        <NavLink to="/manage-users" className={({ isActive }) => (isActive ? 'active' : '')}>
                          <FaUser />
                          <span>Manage Users</span>
                        </NavLink>
                      </li>
                    )}
                    {isAllowed([3]) && (
                      <li>
                        <NavLink to="/manage-users-sessions" className={({ isActive }) => (isActive ? 'active' : '')}>
                          <FaUser />
                          <span>Manage Users Sessions</span>
                        </NavLink>
                      </li>
                    )}
                    {isAllowed([3]) && (
                      <li>
                        <NavLink to="/manage-roles" className={({ isActive }) => (isActive ? 'active' : '')}>
                          <FaLock />
                          <span>Manage Roles & Permissions</span>
                        </NavLink>
                      </li>
                    )}
                  </ul>
                )}
              </li>
            )}

            {/* System Audits Dropdown */}
            {isAllowed([2, 3]) && (
              <li>
                <div onClick={handleSystemAuditsClick} className="sidebar-dropdown">
                  <FaHistory />
                  <span>System Audits</span>
                  <FaCaretDown />
                </div>
                {systemAuditsOpen && (
                  <ul className="submenu">
                    {isAllowed([2, 3]) && (
                      <li>
                        <NavLink to="/audit-trail" className={({ isActive }) => (isActive ? 'active' : '')}>
                          <FaHistory />
                          <span>Audit Trail</span>
                        </NavLink>
                      </li>
                    )}
                    {isAllowed([3]) && (
                      <li>
                        <NavLink to="/logs" className={({ isActive }) => (isActive ? 'active' : '')}>
                          <FaFileAlt />
                          <span>Logs</span>
                        </NavLink>
                      </li>
                    )}
                    {isAllowed([3]) && (
                      <li>
                        <NavLink to="/retention-policy" className={({ isActive }) => (isActive ? 'active' : '')}>
                          <FaFolder />
                          <span>Retention Policy</span>
                        </NavLink>
                      </li>
                    )}
                  </ul>
                )}
              </li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Sidebar;
