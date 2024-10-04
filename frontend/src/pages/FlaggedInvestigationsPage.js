import React, { useEffect, useState, useCallback } from 'react';
import { Card, Button, Modal, Table, Spinner, Pagination, Alert } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faTrash, faCheck, faEye, faHistory } from '@fortawesome/free-solid-svg-icons';
import api from '../services/api'; // Your Axios instance
import { useNavigate } from 'react-router-dom'; // Import useNavigate

const UnderInvestigationPage = ({ showToast }) => {
  const [investigationRecords, setInvestigationRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [recordsPerPage] = useState(10);
  const [userMap, setUserMap] = useState({});
  const totalPages = Math.ceil(investigationRecords.length / recordsPerPage);
  const localUser = JSON.parse(localStorage.getItem('user'));
  const navigate = useNavigate(); // Initialize useNavigate

  // Fetch records under investigation
  const fetchInvestigationRecords = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/under_investigation/');
      setInvestigationRecords(
        response.data.map(record => ({
          ...record,
          notes_history: Array.isArray(record.notes_history)
            ? record.notes_history
            : (typeof record.notes_history === 'string'
                ? record.notes_history.split('\n')
                : []), // Default to an empty array if neither
        }))
      );

      // Fetch user data for mapping
      const userResponse = await api.get('/users/');
      const users = userResponse.data.users.reduce((map, user) => {
        map[user.id] = user;
        return map;
      }, {});
      setUserMap(users);
    } catch (error) {
      console.error('Error fetching investigation records:', error);
      showToast('error', 'Failed to fetch investigation records.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchInvestigationRecords();
  }, [fetchInvestigationRecords]);

  // Function to handle auto-update
  const handleAutoUpdate = async () => {
    try {
      const response = await api.post('/under_investigation/auto-update');
      showToast('success', response.data.message || 'Records updated successfully.', 'Success');
      fetchInvestigationRecords(); // Refresh records after the update
    } catch (error) {
      console.error('Error during auto-update:', error);
      showToast('error', 'Failed to update records.', 'Error');
    }
  };

  // Open edit modal with selected record data
  const handleOpenEditModal = (record) => {
    setSelectedRecord(record);
    setShowEditModal(true);
  };

  const handleCloseEditModal = () => {
    setShowEditModal(false);
    setSelectedRecord(null);
  };

  // Open history modal
  const handleOpenHistoryModal = (record) => {
    setSelectedRecord(record);
    setShowHistoryModal(true);
  };

  const handleCloseHistoryModal = () => {
    setShowHistoryModal(false);
  };

  // Handle deletion of a record
  const handleDeleteRecord = async (recordId) => {
    try {
      await api.delete(`/under_investigation/${recordId}`);
      setInvestigationRecords((prevRecords) => prevRecords.filter(record => record.id !== recordId));
      showToast('success', 'Record deleted successfully.', 'Success');
    } catch (error) {
      console.error('Error deleting record:', error);
      showToast('error', 'Failed to delete record.', 'Error');
    }
  };

  // Handle submitting edits for a record
  const handleEditRecord = async (updatedRecord) => {
    try {
      const notesHistoryEntry = {
        notes: selectedRecord.notes,
        reason: selectedRecord.reason,
        updated_by_name: localUser.name || 'System',
        updated_by_email: localUser.email || 'system',
        updated_at: new Date().toISOString(),
      };

      // Construct the notes history string with detailed information
      const notesHistoryString = `${notesHistoryEntry.updated_at} - Reason: ${notesHistoryEntry.reason}: ${notesHistoryEntry.notes} - Updated by ${notesHistoryEntry.updated_by_name} (${notesHistoryEntry.updated_by_email})`;

      const completeUpdatedRecord = {
        ...updatedRecord,
        notes_history: [
          ...(selectedRecord.notes_history || []),
          notesHistoryString,
        ],
        updated_by_user_id: localUser.id,
      };

      await api.put(`/under_investigation/${selectedRecord.id}`, completeUpdatedRecord);
      setInvestigationRecords((prevRecords) =>
        prevRecords.map((record) => (record.id === selectedRecord.id ? { ...record, ...completeUpdatedRecord } : record))
      );
      showToast('success', 'Record updated successfully.', 'Success');
      handleCloseEditModal();
    } catch (error) {
      console.error('Error updating record:', error);
      showToast('error', 'Failed to update record.', 'Error');
    }
  };

  // Handle marking a record as resolved
  const handleMarkAsResolved = async (recordId) => {
    try {
      const updatedRecord = {
        resolved: true,
        resolved_at: new Date().toISOString(),
      };
      await api.put(`/under_investigation/${recordId}`, updatedRecord);
      setInvestigationRecords((prevRecords) =>
        prevRecords.map((record) => (record.id === recordId ? { ...record, ...updatedRecord } : record))
      );
      showToast('success', 'Record marked as resolved.', 'Success');
    } catch (error) {
      console.error('Error marking record as resolved:', error);
      showToast('error', 'Failed to mark record as resolved.', 'Error');
    }
  };

  // Calculate the current records to display based on pagination
  const indexOfLastRecord = currentPage * recordsPerPage;
  const indexOfFirstRecord = indexOfLastRecord - recordsPerPage;
  const currentRecords = investigationRecords.slice(indexOfFirstRecord, indexOfLastRecord);

  // Handle pagination
  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
  };

  const handleViewSale = (saleId) => {
    navigate(`/sales/${saleId}`); // Navigate to the sale detail page
  };

  if (loading) return <Spinner animation="border" />;

  return (
    <div>
      <h2>Under Investigation Records</h2>

      {/* Button to trigger auto-update */}
      <Button variant="primary" onClick={handleAutoUpdate} className="mb-3">
        Run Auto Update
      </Button>

      {/* Legend Section */}
      <Alert variant="info" size="lg">
        <strong>Legend:</strong>
        <ul>
          <li><strong>Critical Duplicate Detected:</strong> This indicates that there are multiple records that match certain critical conditions such as phone number, client ID, and policy type.</li>
          <li><strong>Potential Duplicate Detected:</strong> This indicates that there might be possible duplicates based on client phone and policy type.</li>
        </ul>
      </Alert>

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>ID</th>
            <th>Sale ID</th>
            <th>Reason</th>
            <th>Notes</th>
            <th>Flagged At</th>
            <th>Resolved At</th>
            <th>Updated By</th>
            <th>Notes History</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {currentRecords.map((record) => (
            <tr key={record.id}>
              <td>{record.id}</td>
              <td>{record.sale_id}</td>
              <td>{record.reason}</td>
              <td>{record.notes}</td>
              <td>{new Date(record.flagged_at).toLocaleString()}</td>
              <td>{record.resolved_at ? new Date(record.resolved_at).toLocaleString() : 'Not Resolved'}</td>
              <td>{userMap[record.updated_by_user_id]?.name || 'System'}</td>
              <td>
                <Button variant="info" onClick={() => handleOpenHistoryModal(record)}>
                  <FontAwesomeIcon icon={faHistory} /> View History
                </Button>
              </td>
              <td>
                <Button variant="primary" onClick={() => handleViewSale(record.sale_id)}>
                  <FontAwesomeIcon icon={faEye} /> View Sale
                </Button>
                <Button variant="warning" onClick={() => handleOpenEditModal(record)}>
                  <FontAwesomeIcon icon={faEdit} /> Edit
                </Button>
                <Button variant="danger" onClick={() => handleDeleteRecord(record.id)}>
                  <FontAwesomeIcon icon={faTrash} /> Delete
                </Button>
                <Button variant="success" onClick={() => handleMarkAsResolved(record.id)}>
                  <FontAwesomeIcon icon={faCheck} /> Mark as Resolved
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      {/* Modal for Editing a Record */}
      <Modal show={showEditModal} onHide={handleCloseEditModal}>
        <Card style={{ padding: '20px' }}>
          <h5>Edit Investigation Record</h5>
          <form onSubmit={(e) => {
            e.preventDefault();
            handleEditRecord({
              reason: selectedRecord.reason,
              notes: selectedRecord.notes,
            });
          }}>
            <div className="mb-3">
              <label>Reason</label>
              <input
                type="text"
                className="form-control"
                value={selectedRecord?.reason || ''}
                onChange={(e) => setSelectedRecord({ ...selectedRecord, reason: e.target.value })}
              />
            </div>
            <div className="mb-3">
              <label>Notes</label>
              <input
                type="text"
                className="form-control"
                value={selectedRecord?.notes || ''}
                onChange={(e) => setSelectedRecord({ ...selectedRecord, notes: e.target.value })}
              />
            </div>
            <Button type="submit">Save Changes</Button>
          </form>
        </Card>
      </Modal>

      {/* Modal for Viewing Notes History */}
      <Modal show={showHistoryModal} onHide={handleCloseHistoryModal} size="lg">
        <Card style={{ padding: '20px', maxHeight: '70vh', overflowY: 'scroll' }}>
          <h5>Notes History</h5>
          <ul>
            {Array.isArray(selectedRecord?.notes_history) && selectedRecord.notes_history.length > 0 ? (
              selectedRecord.notes_history.map((note, index) => (
                <li key={index}>{note}</li>
              ))
            ) : (
              <li>No history available</li>
            )}
          </ul>
        </Card>
      </Modal>

      {/* Pagination */}
      <Pagination className="justify-content-center mt-4">
        <Pagination.First onClick={() => handlePageChange(1)} disabled={currentPage === 1} />
        <Pagination.Prev onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1} />
        {[...Array(totalPages)].map((_, index) => (
          <Pagination.Item
            key={index + 1}
            active={index + 1 === currentPage}
            onClick={() => handlePageChange(index + 1)}
          >
            {index + 1}
          </Pagination.Item>
        ))}
        <Pagination.Next onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages} />
        <Pagination.Last onClick={() => handlePageChange(totalPages)} disabled={currentPage === totalPages} />
      </Pagination>
    </div>
  );
};

export default UnderInvestigationPage;
