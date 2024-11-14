import React, { useState } from 'react';
import axios from 'axios';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import './App.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function App() {
  const [files, setFiles] = useState([]);
  const [receiptData, setReceiptData] = useState([]);
  const [chartData, setChartData] = useState(null);

  const handleFileChange = (e) => {
    setFiles(e.target.files);
  };

  const handleUpload = async () => {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('receipts', files[i]);
    }

    try {
      const response = await axios.post('http://127.0.0.1:5000/upload', formData);
      setReceiptData(response.data.data);
      generateChartData(response.data.data);
    } catch (error) {
      console.error("Error uploading receipts:", error);
    }
  };

  const generateChartData = (data) => {
    const dateTotals = data.reduce((acc, receipt) => {
      const date = receipt.Date || 'Unknown';
      const itemsWithPrices = receipt.Items.map((item, index) => ({
        item,
        price: receipt.Prices[index] || 0,
      }));
      const total = receipt.Total || receipt.Prices.reduce((sum, price) => sum + price, 0);
      acc[date] = acc[date] || { total: 0, items: [] };
      acc[date].total += total;
      acc[date].items = acc[date].items.concat(itemsWithPrices);
      return acc;
    }, {});

    setChartData({
      labels: Object.keys(dateTotals),
      datasets: [
        {
          label: 'Total Spending by Date',
          data: Object.values(dateTotals).map((data) => data.total),
          backgroundColor: 'rgba(75, 192, 192, 0.6)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1,
        },
      ],
    });
  };

  return (
    <div className="app-container">
      <h1 className="app-title slide-down">Receipt Analyzer</h1>
      <div className="upload-section fade-in">
        <input type="file" multiple onChange={handleFileChange} className="file-input" />
        <button onClick={handleUpload} className="upload-button">Analyze Receipts</button>
      </div>
      
      {receiptData.length > 0 && (
        <div className="results-section fade-in">
          <h2>Parsed Receipt Data</h2>
          {receiptData.map((receipt, index) => (
            <div key={index} className="receipt fade-in">
              <h3>Date: {receipt.Date || "Unknown"}</h3>
              <ul>
                {receipt.Items.map((item, i) => (
                  <li key={i}>
                    {item}: ${receipt.Prices[i]}
                  </li>
                ))}
              </ul>
              <p><strong>Total:</strong> ${receipt.Total || receipt.Prices.reduce((sum, price) => sum + price, 0)}</p>
            </div>
          ))}
        </div>
      )}

      {chartData && (
        <div className="chart-container fade-in">
          <h2>Spending Trends</h2>
          <Bar data={chartData} options={{ responsive: true }} />
        </div>
      )}
    </div>
  );
}

export default App;
