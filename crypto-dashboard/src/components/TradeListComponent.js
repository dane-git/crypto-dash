const TradeListComponent = ({ trades }) => {
  if (!trades || trades.length === 0) {
    return <p>Loading trades...</p>;
  }

  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr>
          <th style={{ borderBottom: "2px solid #ddd", textAlign: "left", padding: "10px" }}>
            Trade ID
          </th>
          <th style={{ borderBottom: "2px solid #ddd", textAlign: "left", padding: "10px" }}>
            Price
          </th>
          <th style={{ borderBottom: "2px solid #ddd", textAlign: "left", padding: "10px" }}>
            Size
          </th>
          <th style={{ borderBottom: "2px solid #ddd", textAlign: "left", padding: "10px" }}>
            Side
          </th>
        </tr>
      </thead>
      <tbody>
        {trades.map((trade) => (
          <tr key={trade.trade_id}>
            <td style={{ padding: "10px", borderBottom: "1px solid #ddd" }}>{trade.trade_id}</td>
            <td style={{ padding: "10px", borderBottom: "1px solid #ddd" }}>${trade.price}</td>
            <td style={{ padding: "10px", borderBottom: "1px solid #ddd" }}>{trade.size}</td>
            <td
              style={{
                padding: "10px",
                borderBottom: "1px solid #ddd",
                color: trade.side === "BUY" ? "green" : "red",
              }}
            >
              {trade.side}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default TradeListComponent;