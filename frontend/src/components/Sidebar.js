import React from 'react';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTachometerAlt, faFileAlt, faChartLine, faUsers, faExclamationTriangle, faUserTie, faBuilding, faFileInvoice, faLock, faDatabase, faTools } from '@fortawesome/free-solid-svg-icons';
import './Sidebar.css';  // Import the custom CSS

function Sidebar() {
  const userRole = localStorage.getItem('userRole');  // Get the user's role from localStorage

  return (
    <div className="sidebar">
      <ul className="list-unstyled">
        {/* All Users */}
        <li>
          <Link to="/dashboard">
            <FontAwesomeIcon icon={faTachometerAlt} /> Dashboard
          </Link>
        </li>
        <li>
          <Link to="/reports">
            <FontAwesomeIcon icon={faFileAlt} /> Reports
          </Link>
        </li>
        <li>
          <Link to="/incepted-sales">
            <FontAwesomeIcon icon={faChartLine} /> Incepted Sales
          </Link>
        </li>
        <li>
          <Link to="/sales">
            <FontAwesomeIcon icon={faFileInvoice} /> Sales
          </Link>
        </li>
        <li>
          <Link to="/queries">
            <FontAwesomeIcon icon={faExclamationTriangle} /> Queries
          </Link>
        </li>
        <li>
          <Link to="/sales-executives">
            <FontAwesomeIcon icon={faUserTie} /> Sales Executive Information
          </Link>
        </li>
        <li>
          <Link to="/investigations">
            <FontAwesomeIcon icon={faUsers} /> Flagged for Investigations
          </Link>
        </li>

        {/* Managers and Admins */}
        {(userRole === 'manager' || userRole === 'admin') && (
          <>
            <li>
              <Link to="/audit-trail">
                <FontAwesomeIcon icon={faFileAlt} /> Audit Trail
              </Link>
            </li>
            <li>
              <Link to="/update-user-info">
                <FontAwesomeIcon icon={faUsers} /> Update User Information
              </Link>
            </li>
            <li>
              <Link to="/products">
                <FontAwesomeIcon icon={faTools} /> Manage Products
              </Link>
            </li>
            <li>
              <Link to="/banks">
                <FontAwesomeIcon icon={faBuilding} /> Manage Banks
              </Link>
            </li>
            <li>
              <Link to="/branches">
                <FontAwesomeIcon icon={faBuilding} /> Manage Branches
              </Link>
            </li>
            <li>
              <Link to="/bank-branches">
                <FontAwesomeIcon icon={faBuilding} /> Manage Bank Branches
              </Link>
            </li>
            <li>
              <Link to="/paypoints">
                <FontAwesomeIcon icon={faBuilding} /> Manage Paypoints
              </Link>
            </li>
          </>
        )}

        {/* Admin Only */}
        {userRole === 'admin' && (
          <>
            <li>
              <Link to="/logs">
                <FontAwesomeIcon icon={faDatabase} /> Logs
              </Link>
            </li>
            <li>
              <Link to="/retention-policy">
                <FontAwesomeIcon icon={faLock} /> Update Retention Policy
              </Link>
            </li>
            <li>
              <Link to="/manage-access">
                <FontAwesomeIcon icon={faLock} /> Manage Access & Roles
              </Link>
            </li>
          </>
        )}
      </ul>
    </div>
  );
}

export default Sidebar;
