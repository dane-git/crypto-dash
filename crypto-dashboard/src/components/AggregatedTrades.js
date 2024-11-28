import React from "react";
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, Legend } from "recharts";
import "./AggregatedTrades.css"; // Import CSS for responsive styling

const AggregatedTrades = ({ productId, aggData }) => {
  if (!aggData[productId]) return null;

  const intervals = ["1m", "5m", "10m", "60m"];
  const data = intervals.map((interval) => {
    const buys = aggData[productId][interval]?.buys || { avg_price: 0, total_size: 0 };
    const sells = aggData[productId][interval]?.sells || { avg_price: 0, total_size: 0 };

    return {
      interval,
      buyVolume: buys.avg_price * buys.total_size,
      sellVolume: sells.avg_price * sells.total_size,
    };
  });

  return (
    <div className="aggregated-trades">
      {data.map((entry, index) => (
        <BarChart
          key={index}
          width={175}
          height={200}
          data={[entry]} // Each chart gets one data point
          margin={{ top: 5, right: 10, left: 10, bottom: 5, padding: 0}}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="interval" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="buyVolume" stackId="a" fill="green" name="Buy Volume" />
          <Bar dataKey="sellVolume" stackId="a" fill="red" name="Sell Volume" />
        </BarChart>
      ))}
    </div>
  );
};

export default AggregatedTrades;
