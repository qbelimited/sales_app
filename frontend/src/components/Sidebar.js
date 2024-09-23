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
  FaWarehouse,
  FaCaretDown,
  FaFileAlt,
  FaLock,
  FaHistory,
  FaUser,
  FaCog,
  FaFolder,
} from 'react-icons/fa';
import './Sidebar.css';

function Sidebar() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [systemAuditsOpen, setSystemAuditsOpen] = useState(false);
  const [manageItemsOpen, setManageItemsOpen] = useState(false);
  const [salesOpen, setSalesOpen] = useState(false);

  // Handle clicking on the settings
  const handleSettingsClick = () => {
    setSettingsOpen(!settingsOpen);
  };

  // Handle clicking on the system audits
  const handleSystemAuditsClick = () => {
    setSystemAuditsOpen(!systemAuditsOpen);
  };

  // Handle clicking on manage items
  const handleManageItemsClick = () => {
    setManageItemsOpen(!manageItemsOpen);
  };

  // Handle clicking on sales
  const handleSalesClick = () => {
    setSalesOpen(!salesOpen);
  };

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

          {/* Sales Dropdown */}
          <li>
            <div onClick={handleSalesClick} className="sidebar-dropdown">
              <FaChartBar />
              <span>Manage Sales</span>
              <FaCaretDown />
            </div>
            {salesOpen && (
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
                  <NavLink to="/flagged-investigations" className={({ isActive }) => (isActive ? 'active' : '')}>
                    <FaFlag />
                    <span>Flagged Investigations</span>
                  </NavLink>
                </li>
              </ul>
            )}
          </li>

          {/* Manage Items Dropdown */}
          <li>
            <div onClick={handleManageItemsClick} className="sidebar-dropdown">
              <FaTasks />
              <span> Manage Items</span>
              <FaCaretDown />
            </div>
            {manageItemsOpen && (
              <ul className="submenu">
                <li>
                  <NavLink to="/manage-banks" className={({ isActive }) => (isActive ? 'active' : '')}>
                    <FaBuilding />
                    <span>Manage Banks</span>
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
                <li>
                  <NavLink to="/manage-paypoints" className={({ isActive }) => (isActive ? 'active' : '')}>
                    <FaSearch />
                    <span>Manage Paypoints</span>
                  </NavLink>
                </li>
              </ul>
            )}
          </li>

          {/* Settings Dropdown */}
          <li>
            <div onClick={handleSettingsClick} className="sidebar-dropdown">
              <FaCog />
              <span> Settings</span>
              <FaCaretDown />
            </div>
            {settingsOpen && (
              <ul className="submenu">
                <li>
                  <NavLink to="/manage-users" className={({ isActive }) => (isActive ? 'active' : '')}>
                    <FaUser />
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

          {/* System Audits Dropdown */}
          <li>
            <div onClick={handleSystemAuditsClick} className="sidebar-dropdown">
              <FaHistory />
              <span>System Audits</span>
              <FaCaretDown />
            </div>
            {systemAuditsOpen && (
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
        </ul>
      </div>
    </div>
  );
}

export default Sidebar;
