import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './AggregationsChart.css';

function AggregationsChart({ aggregations }) {
  if (!aggregations || !aggregations.groups) {
    return null;
  }

  const data = Object.entries(aggregations.groups).map(([name, value]) => ({
    name: name.length > 30 ? name.substring(0, 30) + '...' : name,
    fullName: name,
    count: value,
  }));

  return (
    <div className="aggregations-chart">
      <h3>Aggregations</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="name" 
            angle={-45}
            textAnchor="end"
            height={100}
          />
          <YAxis />
          <Tooltip 
            formatter={(value, name, props) => [
              value,
              props.payload.fullName
            ]}
          />
          <Legend />
          <Bar dataKey="count" fill="#667eea" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default AggregationsChart;

