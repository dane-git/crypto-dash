
import React from "react";
import Plot from "react-plotly.js";

const GraphComponent = ({ data }) => {
  if (!data || data.length === 0) {
    return <p>Loading graph...</p>;
  }

  // Extract prices from the data
  const prices = data.map((d) => d.price);

  // Compute min and max prices
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);

  // Add 10% padding
  const padding = (maxPrice - minPrice) * 0.1;
  const yMin = minPrice - padding;
  const yMax = maxPrice + padding;

  return (
    <Plot
      data={[
        {
          x: data.map((d) => d.time),
          y: prices,
          type: "scatter",
          mode: "lines",
          name: "Price",
        },
      ]}
      layout={{
        title: "Price Chart",
        xaxis: { title: "Time" },
        yaxis: { title: "Price", range: [yMin, yMax] }, // Adjust y-axis range
        margin: { t: 40, l: 40, r: 40, b: 40 },
      }}
      style={{ width: "100%", height: "400px" }}
    />
  );
};

export default GraphComponent;


// import React from "react";
// import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

// const GraphComponent = ({ data }) => {
//   if (!data || data.length === 0) {
//     return <p>Loading graph...</p>;
//   }

//   const formattedData = data.map((item) => ({
//     time: new Date(item.time).toLocaleTimeString(),
//     price: parseFloat(item.price),
//   }));

//   return (
//     <LineChart width={500} height={300} data={formattedData}>
//       <XAxis dataKey="time" />
//       <YAxis />
//       <Tooltip />
//       <CartesianGrid stroke="#eee" strokeDasharray="5 5" />
//       <Line type="monotone" dataKey="price" stroke="#8884d8" />
//     </LineChart>
//   );
// };

// export default GraphComponent;
