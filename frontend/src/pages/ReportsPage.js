import React, { useState, useRef } from 'react';
import { Table, Button, Form, Row, Col, Spinner, Card } from 'react-bootstrap';
import api from '../services/api';
import { CSVLink } from 'react-csv';
import { Chart, registerables } from 'chart.js';
import { Bar, Line, Pie } from 'react-chartjs-2';
import * as d3 from 'd3';
import jsPDF from 'jspdf'; // Import jsPDF for PDF export
import autoTable from 'jspdf-autotable'; // Import autoTable for table export in PDF
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFileCsv, faFilePdf, faChartBar, faChartLine, faChartPie } from '@fortawesome/free-solid-svg-icons';

Chart.register(...registerables);

const aggregateFields = [
  'sale_manager_name',
  'sales_executive_name',
  'sales_executive_branch',
  'product_name',
  'product_category',
  'product_group',
  'bank_name',
  'bank_branch_name',
  'paypoint_name',
  'source_type',
  'collection_platform',
  'status',
  'customer_called',
  'momo_first_premium'
];

const ReportsPage = ({ showToast }) => {
  const [filters, setFilters] = useState({ startDate: '', endDate: '', aggregateBy: '' });
  const [reportData, setReportData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [chartData, setChartData] = useState({ labels: [], datasets: [] });
  const [chartType, setChartType] = useState('bar');
  const chartRef = useRef(null); // Ref for capturing chart

  const handlePreview = async () => {
    if (!filters.startDate || !filters.endDate) {
      showToast('warning', 'Please fill in all required fields.', 'Warning');
      return;
    }

    if (new Date(filters.startDate) > new Date(filters.endDate)) {
      showToast('warning', 'End date must be later than start date.', 'Warning');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/reports/sales', {
        filters: {
          start_date: filters.startDate,
          end_date: filters.endDate,
        },
        aggregate_by: filters.aggregateBy || 'None',
      }, {
        params: {
          sort_order: 'desc',
          sort_by: 'created_at',
          per_page: 10,
          page: 1,
        },
      });

      const parsedData = d3.csvParse(response.data);

      if (parsedData && parsedData.length > 0) {
        setReportData(parsedData);
        setChartData(generateChartData(parsedData));
      } else {
        showToast('info', 'No data found for the selected filters.', 'Info');
        setReportData([]);
      }
    } catch (error) {
      console.error("Error fetching report data:", error);
      showToast('danger', 'Failed to fetch report data.', 'Error');
    } finally {
      setLoading(false);
    }
  };

  const exportToPDF = () => {
    const doc = new jsPDF('landscape'); // Set to landscape orientation
    doc.setFontSize(22);
    doc.text('Sales Report', 14, 20); // Title
    doc.setFontSize(12);

    // Adding some space before the table
    doc.text(`Report Date: ${new Date().toLocaleDateString()}`, 14, 30);
    doc.text(`Date Range: ${filters.startDate} to ${filters.endDate}`, 14, 40);
    doc.setFontSize(10);

    // Prepare the data for the table
    const columns = Object.keys(reportData[0]).map(key => ({
      header: key,
      dataKey: key,
      width: 30 // Adjust width to fit more data
    }));

    // Generate the auto table
    autoTable(doc, {
      head: [columns],
      body: reportData.map(row => Object.keys(row).map(key => row[key])),
      startY: 50,
      margin: { horizontal: 10 },
      styles: {
        fontSize: 8, // Smaller font size for better fit
        cellPadding: 2, // Reduced padding for smaller row height
        overflow: 'linebreak',
        lineWidth: 0.5,
        lineColor: [44, 62, 80],
        fillColor: [244, 244, 244],
      },
      headStyles: {
        fillColor: [52, 152, 219], // Header color
        textColor: [255, 255, 255],
        fontSize: 9,
        fontStyle: 'bold',
      },
      alternateRowStyles: {
        fillColor: [220, 220, 220], // Alternate row color
      },
      theme: 'striped', // Add striping for better readability
      pageBreak: 'avoid', // Prevent page breaks within rows
    });

    // Save the document
    doc.save('sales_report.pdf');
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  const generateChartData = (data) => {
    if (!data || data.length === 0) {
      return { labels: [], datasets: [] };
    }

    // Generate different colors for the bars
    const colors = ['rgba(255, 99, 132, 0.5)', 'rgba(54, 162, 235, 0.5)', 'rgba(255, 206, 86, 0.5)',
                    'rgba(75, 192, 192, 0.5)', 'rgba(153, 102, 255, 0.5)', 'rgba(255, 159, 64, 0.5)'];

    return {
      labels: data.map(item => item.client_name || 'Unknown'),
      datasets: [{
        label: 'Amount',
        data: data.map(item => parseFloat(item.amount) || 0),
        backgroundColor: colors.slice(0, data.length), // Limit colors based on the number of data points
        borderColor: colors.slice(0, data.length).map(color => color.replace('0.5', '1')), // Darker borders
        borderWidth: 1,
      }],
    };
  };

  return (
    <div className="container mt-5">
      <h2 className="text-center mb-4">Generate Reports</h2>

      <Card className="mb-4">
        <Card.Body>
          <Form>
            <Row>
              <Col xs={12} md={4}>
                <Form.Group controlId="filterStartDate">
                  <Form.Label>Start Date</Form.Label>
                  <Form.Control type="date" name="startDate" onChange={handleFilterChange} />
                </Form.Group>
              </Col>
              <Col xs={12} md={4}>
                <Form.Group controlId="filterEndDate">
                  <Form.Label>End Date</Form.Label>
                  <Form.Control type="date" name="endDate" onChange={handleFilterChange} />
                </Form.Group>
              </Col>
              <Col xs={12} md={4}>
                <Form.Group controlId="aggregateBy">
                  <Form.Label>Aggregate By</Form.Label>
                  <Form.Control as="select" name="aggregateBy" onChange={handleFilterChange}>
                    <option value="">Select Aggregate Field</option>
                    <option value="none">None</option>
                    {aggregateFields.map(field => (
                      <option key={field} value={field}>{field.replace(/_/g, ' ')}</option>
                    ))}
                  </Form.Control>
                </Form.Group>
              </Col>
              <Col xs={12} className="align-self-end mt-2">
                <Button variant="primary" onClick={handlePreview} disabled={loading}>
                  {loading ? <Spinner animation="border" size="sm" /> : 'Preview'}
                </Button>
              </Col>
            </Row>
          </Form>
        </Card.Body>
      </Card>

      <Card className="mt-4">
        <Card.Body>
          <Form.Group controlId="chartType">
            <Form.Label>Select Chart Type</Form.Label>
            <Form.Control as="select" size="sm" value={chartType} onChange={(e) => setChartType(e.target.value)}>
              <option value="bar"><FontAwesomeIcon icon={faChartBar} /> Bar Chart</option>
              <option value="line"><FontAwesomeIcon icon={faChartLine} /> Line Chart</option>
              <option value="pie"><FontAwesomeIcon icon={faChartPie} /> Pie Chart</option>
            </Form.Control>
          </Form.Group>
          <div style={{ position: 'relative', height: '400px' }}>
            {chartType === 'bar' && <Bar ref={chartRef} data={chartData} options={{ responsive: true }} />}
            {chartType === 'line' && <Line ref={chartRef} data={chartData} options={{ responsive: true }} />}
            {chartType === 'pie' && <Pie ref={chartRef} data={chartData} options={{ responsive: true }} />}
          </div>
        </Card.Body>
      </Card>

      <div className="mt-4">
        {reportData.length > 0 ? (
          <>
            {/* Buttons for CSV and PDF downloads above the table */}
            <div className="d-flex justify-content-between mb-3">
              <CSVLink data={reportData} filename={"report_preview.csv"}>
                <Button variant="success">
                  <FontAwesomeIcon icon={faFileCsv} /> Download CSV
                </Button>
              </CSVLink>
              <Button variant="primary" onClick={exportToPDF} disabled={loading}>
                {loading ? <Spinner animation="border" size="sm" /> : <FontAwesomeIcon icon={faFilePdf} />} Download PDF
              </Button>
            </div>

            <Table id="reportTable" striped bordered hover responsive>
              <thead>
                <tr>
                  {Object.keys(reportData[0]).map((key) => (
                    <th key={key}>{key.replace(/_/g, ' ')}</th> // Replace underscores with spaces for display
                  ))}
                </tr>
              </thead>
              <tbody>
                {reportData.map((row, index) => (
                  <tr key={index}>
                    {Object.values(row).map((value, idx) => (
                      <td key={idx}>{value}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </Table>
          </>
        ) : (
          <p>No report data available.</p>
        )}
      </div>
    </div>
  );
};

export default ReportsPage;

