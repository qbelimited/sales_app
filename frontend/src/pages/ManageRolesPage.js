import React, { useState, useEffect, useCallback } from 'react';
import { Table, Spinner, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import { FaPen, FaTrash } from 'react-icons/fa';
import api from '../services/api';

const ManageRolesPage = ({ showToast }) => {
  const [roles, setRoles] = useState([]);
  const [accessList, setAccessList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [currentRole, setCurrentRole] = useState(null);
  const [roleName, setRoleName] = useState('');
  const [roleDescription, setRoleDescription] = useState('');
  const [showAccessModal, setShowAccessModal] = useState(false);
  const [currentAccess, setCurrentAccess] = useState({
    role_id: '',
    can_create: false,
    can_update: false,
    can_delete: false,
    can_view_logs: false,
    can_manage_users: false,
    can_view_audit_trail: false,
  });
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [roleToDelete, setRoleToDelete] = useState(null);

  // Fetch all roles and access
  const fetchRolesAndAccess = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch roles
      const rolesResponse = await api.get('/roles/');
      setRoles(rolesResponse.data || []);

      // Fetch access list
      const accessResponse = await api.get('/access/');
      setAccessList(accessResponse.data || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to fetch data. Please try again later.');
      showToast('danger', 'Failed to fetch data. Please try again later.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchRolesAndAccess();
  }, [fetchRolesAndAccess]);

  // Handle create/update role
  const handleSaveRole = async () => {
    try {
      if (currentRole) {
        // Update existing role
        await api.put(`/roles/${currentRole.id}`, {
          name: roleName,
          description: roleDescription,
        });
        showToast('success', 'Role updated successfully!', 'Success');
      } else {
        // Create new role
        await api.post('/roles/', {
          name: roleName,
          description: roleDescription,
        });
        showToast('success', 'Role created successfully!', 'Success');
      }
      fetchRolesAndAccess();
      setShowModal(false);
      setRoleName('');
      setRoleDescription('');
      setCurrentRole(null);
    } catch (error) {
      console.error('Error saving role:', error);
      showToast('danger', 'Failed to save role. Please try again.', 'Error');
    }
  };

  // Handle create/update access
  const handleSaveAccess = async () => {
    try {
      if (currentAccess.role_id) {
        // Update existing access
        const response = await api.put(`/access/${currentAccess.role_id}`, {
          ...currentAccess,
          role_id: parseInt(currentAccess.role_id, 10),
        });
        console.log(response.data);
        showToast('success', 'Access updated successfully!', 'Success');
      } else {
        // Create new access
        const response = await api.post('/access/', {
          ...currentAccess,
          role_id: parseInt(currentAccess.role_id, 10),
        });
        console.log(response.data);
        showToast('success', 'Access created successfully!', 'Success');
      }
      fetchRolesAndAccess();
      setShowAccessModal(false);
      setCurrentAccess({
        role_id: '',
        can_create: false,
        can_update: false,
        can_delete: false,
        can_view_logs: false,
        can_manage_users: false,
        can_view_audit_trail: false,
      });
    } catch (error) {
      console.error('Error saving access:', error.response ? error.response.data : error.message);

      // Check for specific error status
      if (error.response && error.response.status === 401) {
        showToast('danger', 'Unauthorized. Please log in again.', 'Error');
      } else if (error.response && error.response.status === 403) {
        showToast('danger', 'Forbidden. You do not have permission to update access.', 'Error');
      } else {
        showToast('danger', 'Failed to save access. Please try again.', 'Error');
      }
    }
  };

  // Handle delete role and its access
  const handleDeleteRole = async () => {
    setShowDeleteModal(false);
    try {
      // Check if role has access
      const access = accessList.find((access) => access.role_id === roleToDelete.id);

      // Delete role
      await api.delete(`/roles/${roleToDelete.id}`);

      // Delete associated access if it exists
      if (access) {
        await api.delete('/access/', { data: { role_id: roleToDelete.id } });
      }

      showToast('success', 'Role and associated access deleted successfully!', 'Success');
      fetchRolesAndAccess();
    } catch (error) {
      console.error('Error deleting role or access:', error);
      showToast('danger', 'Failed to delete role and access. Please try again.', 'Error');
    }
  };

  // Handle edit role
  const handleEditRole = (role) => {
    setCurrentRole(role);
    setRoleName(role.name);
    setRoleDescription(role.description);
    setShowModal(true);
  };

  // Handle show delete access modal
  const handleShowDeleteRoleModal = (role) => {
    setRoleToDelete(role);
    setShowDeleteModal(true);
  };

  // Handle edit access
  const handleEditAccess = (access) => {
    setCurrentAccess(access);
    setShowAccessModal(true);
  };

  if (loading) return <Spinner animation="border" />;

  return (
    <div style={{ marginTop: '20px', padding: '20px' }}>
      <Row className="mb-3">
        <Col>
          <h2>Manage Roles</h2>
        </Col>
        <Col className="text-right">
          <Button onClick={() => setShowModal(true)}>Create New Role</Button>
        </Col>
      </Row>

      {error && <p className="text-center text-danger">{error}</p>}

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>#</th>
            <th>Role Name</th>
            <th>Description</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {roles.length > 0 ? (
            roles.map((role, index) => (
              <tr key={role.id}>
                <td>{index + 1}</td>
                <td>{role.name}</td>
                <td>{role.description}</td>
                <td>
                  <Button variant="link" size="sm" onClick={() => handleEditRole(role)}>
                    <FaPen />
                  </Button>
                  <Button variant="link" size="sm" onClick={() => handleShowDeleteRoleModal(role)}>
                    <FaTrash />
                  </Button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="4" className="text-center">No roles found</td>
            </tr>
          )}
        </tbody>
      </Table>

      {/* Access Management Section */}
      <Row className="mt-5 mb-3">
        <Col>
          <h2>Access Management</h2>
        </Col>
        <Col className="text-right">
          <Button onClick={() => setShowAccessModal(true)}>Create New Access</Button>
        </Col>
      </Row>

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>Role Name</th>
            <th>Can Create</th>
            <th>Can Update</th>
            <th>Can Delete</th>
            <th>Can View Logs</th>
            <th>Can Manage Users</th>
            <th>Can View Audit Trail</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {accessList.length > 0 ? (
            accessList.map((access) => {
              const role = roles.find(r => r.id === access.role_id);
              return (
                <tr key={access.role_id}>
                  <td>{role ? role.name : 'Role Not Found'}</td>
                  <td>{access.can_create ? 'Yes' : 'No'}</td>
                  <td>{access.can_update ? 'Yes' : 'No'}</td>
                  <td>{access.can_delete ? 'Yes' : 'No'}</td>
                  <td>{access.can_view_logs ? 'Yes' : 'No'}</td>
                  <td>{access.can_manage_users ? 'Yes' : 'No'}</td>
                  <td>{access.can_view_audit_trail ? 'Yes' : 'No'}</td>
                  <td>
                    <Button variant="link" size="sm" onClick={() => handleEditAccess(access)}>
                      <FaPen />
                    </Button>
                    <Button variant="link" size="sm" onClick={() => handleShowDeleteRoleModal(role)}>
                      <FaTrash />
                    </Button>
                  </td>
                </tr>
              );
            })
          ) : (
            <tr>
              <td colSpan="8" className="text-center">No access records found</td>
            </tr>
          )}
        </tbody>
      </Table>

      {/* Create/Edit Role Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>{currentRole ? 'Edit Role' : 'Create Role'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group>
              <Form.Label>Role Name</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter role name"
                value={roleName}
                onChange={(e) => setRoleName(e.target.value)}
              />
            </Form.Group>
            <Form.Group>
              <Form.Label>Description</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter description"
                value={roleDescription}
                onChange={(e) => setRoleDescription(e.target.value)}
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Close
          </Button>
          <Button variant="primary" onClick={handleSaveRole}>
            {currentRole ? 'Update Role' : 'Create Role'}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Create/Edit Access Modal */}
      <Modal show={showAccessModal} onHide={() => setShowAccessModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>{currentAccess.role_id ? 'Edit Access' : 'Create Access'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group>
              <Form.Label>Role</Form.Label>
              <Form.Control
                as="select"
                value={currentAccess.role_id}
                onChange={(e) => setCurrentAccess({ ...currentAccess, role_id: parseInt(e.target.value, 10) })}
                disabled={!!currentAccess.role_id} // Disable if editing
              >
                <option value="">Select a Role</option>
                {roles.map(role => (
                  <option key={role.id} value={role.id}>{role.name}</option>
                ))}
              </Form.Control>
            </Form.Group>
            <Form.Group>
              <Form.Check
                type="checkbox"
                label="Can Create"
                checked={currentAccess.can_create}
                onChange={(e) => setCurrentAccess({ ...currentAccess, can_create: e.target.checked })}
              />
              <Form.Check
                type="checkbox"
                label="Can Update"
                checked={currentAccess.can_update}
                onChange={(e) => setCurrentAccess({ ...currentAccess, can_update: e.target.checked })}
              />
              <Form.Check
                type="checkbox"
                label="Can Delete"
                checked={currentAccess.can_delete}
                onChange={(e) => setCurrentAccess({ ...currentAccess, can_delete: e.target.checked })}
              />
              <Form.Check
                type="checkbox"
                label="Can View Logs"
                checked={currentAccess.can_view_logs}
                onChange={(e) => setCurrentAccess({ ...currentAccess, can_view_logs: e.target.checked })}
              />
              <Form.Check
                type="checkbox"
                label="Can Manage Users"
                checked={currentAccess.can_manage_users}
                onChange={(e) => setCurrentAccess({ ...currentAccess, can_manage_users: e.target.checked })}
              />
              <Form.Check
                type="checkbox"
                label="Can View Audit Trail"
                checked={currentAccess.can_view_audit_trail}
                onChange={(e) => setCurrentAccess({ ...currentAccess, can_view_audit_trail: e.target.checked })}
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowAccessModal(false)}>
            Close
          </Button>
          <Button variant="primary" onClick={handleSaveAccess}>
            {currentAccess.role_id ? 'Update Access' : 'Create Access'}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Delete Access/Role Modal */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Deletion</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to delete this role? Any associated access will also be deleted.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDeleteRole}>
            Confirm Delete
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default ManageRolesPage;
