import React from 'react';
import { Modal, Button } from 'react-bootstrap';

const HelpArticleModal = ({ article, onClose }) => {
  return (
    <Modal show onHide={onClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>{article.title}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <img src={article.imageUrl} alt={article.title} className="img-fluid mb-3" />
        <p>{article.content}</p>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>Close</Button>
      </Modal.Footer>
    </Modal>
  );
};

export default HelpArticleModal;
