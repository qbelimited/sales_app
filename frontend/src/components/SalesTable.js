import React from 'react';
import { Table, Button } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faTrash } from '@fortawesome/free-solid-svg-icons';

const SalesTable = ({ salesRecords, onEdit, onDelete }) => {
  return (
    <div className="mt-5">
      <h2>Current Sales</h2>
      <Table striped bordered hover className="mt-3">
        <thead>
          <tr>
            <th>#</th>
            <th>Client Name</th>
            <th>Phone</th>
            <th>Amount</th>
            <th>Policy Type</th>
            <th>Source Type</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {salesRecords.length > 0 ? (
            salesRecords.map((sale, index) => (
              <tr key={sale.id}>
                <td>{index + 1}</td>
                <td>{sale.client_name}</td>
                <td>{sale.client_phone}</td>
                <td>{sale.amount}</td>
                <td>{sale.policy_type_id}</td>
                <td>{sale.source_type}</td>
                <td>{sale.status}</td> {/* Added status column */}
                <td>
                  <Button
                    variant="warning"
                    size="sm"
                    className="me-2"
                    onClick={() => onEdit(sale)}
                  >
                    <FontAwesomeIcon icon={faEdit} />
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => onDelete(sale.id)}
                  >
                    <FontAwesomeIcon icon={faTrash} />
                  </Button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="8" className="text-center">
                No sales records available.
              </td>
            </tr>
          )}
        </tbody>
      </Table>
    </div>
  );
};

export default SalesTable;
