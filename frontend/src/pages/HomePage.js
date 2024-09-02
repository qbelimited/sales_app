import React from 'react';
import { Link } from 'react-router-dom';  // Add this import

function HomePage() {
  return (
    <div className="container mt-5">
      <div className="jumbotron text-center">
        <h1 className="display-4">Welcome to the Sales Recording App</h1>
        <p className="lead">Manage and track your sales efficiently with our system.</p>
        <hr className="my-4" />
        <p>Navigate through the menu to manage sales, view reports, and more.</p>
        <Link className="btn btn-primary btn-lg" to="/sales" role="button">Get Started</Link>
      </div>
    </div>
  );
}

export default HomePage;
