import React, { useState, useEffect, useRef } from "react";
import GraphComponent from "./components/GraphComponent";
import TradeListComponent from "./components/TradeListComponent";
import AggregatedTrades from "./components/AggregatedTrades";
import axiosInstance from "./axios";
import "./App.css"
const coins = ["BTC-USD", "ETH-USD", "ADA-USD", "MUSE-USD"];

const App = () => {
  const [graphData, setGraphData] = useState({});
  const [tradeData, setTradeData] = useState({});
  const [aggData, setAggData] = useState({})
  const requestQueue = useRef([]);
  const isProcessingQueue = useRef(false);

  const addToQueue = (endpoint, params, resolve, reject) => {
    requestQueue.current.push({ endpoint, params, resolve, reject });
    processQueue();
  };

  const processQueue = () => {
    if (isProcessingQueue.current || requestQueue.current.length === 0) return;

    isProcessingQueue.current = true;

    const { endpoint, params, resolve, reject } = requestQueue.current.shift();

    axiosInstance
      .get(endpoint, { params })
      .then((response) => {
        resolve(response.data);
      })
      .catch((error) => {
        console.error("Request failed:", error);
        reject(error);
      })
      .finally(() => {
        isProcessingQueue.current = false;
        setTimeout(processQueue, 1000); // Delay next request by 1 second
      });
  };

  const fetchData = async () => {
    try {
      const startOfDay = new Date();
      startOfDay.setHours(0, 0, 0, 0);
      const startTime = new Date();
      const startTime1m = new Date()
      const startTime5m = new Date()
      const startTime10m = new Date()
      const startTime60m = new Date()

      startTime1m.setSeconds(startTime.getSeconds() - 60);
      startTime5m.setSeconds(startTime.getSeconds() - 600);
      startTime10m.setSeconds(startTime.getSeconds() - 600);
      startTime60m.setSeconds(startTime.getSeconds() - 3600);
      const graphPromises = coins.map(
        (coin) =>
          new Promise((resolve, reject) => {
            addToQueue("/ticker_data", { product_id: coin, start_time: startOfDay.toISOString() }, resolve, reject);
          })
      );

    //   const tradePromises = coins.map(
    //     (coin) =>
    //       new Promise((resolve, reject) => {
    //         addToQueue("/recent_trades", { product_id: coin, limit: 10 }, resolve, reject);
    //       })
    //   );
  
      const aggPromises1 = coins.map(
        (coin) =>
          new Promise((resolve, reject) => {
            addToQueue("/aggregated_trades", { product_id: coin, since: startTime1m }, resolve, reject);
          })
      );
      const aggPromises5 = coins.map(
        (coin) =>
          new Promise((resolve, reject) => {
            addToQueue("/aggregated_trades", { product_id: coin, since: startTime5m }, resolve, reject);
          })
      );
      const aggPromises10 = coins.map(
        (coin) =>
          new Promise((resolve, reject) => {
            addToQueue("/aggregated_trades", { product_id: coin, since: startTime10m }, resolve, reject);
          })
      );
      const aggPromises60 = coins.map(
        (coin) =>
          new Promise((resolve, reject) => {
            addToQueue("/aggregated_trades", { product_id: coin, since: startTime60m }, resolve, reject);
          })
      );

      const graphResults = await Promise.all(graphPromises);
    //   const tradeResults = await Promise.all(tradePromises);
      const aggResults1 = await Promise.all(aggPromises1)
      const aggResults5 = await Promise.all(aggPromises5)
      const aggResults10 = await Promise.all(aggPromises10)
      const aggResults60 = await Promise.all(aggPromises60)

      const newGraphData = coins.reduce((acc, coin, i) => {
        acc[coin] = graphResults[i];
        return acc;
      }, {});

    //   const newTradeData = coins.reduce((acc, coin, i) => {
    //     acc[coin] = tradeResults[i];
    //     return acc;
    //   }, {});

      const newAggData = coins.reduce((acc, coin,i) => {
        acc[coin] = {}
        acc[coin]['1m'] = aggResults1[i];
        acc[coin]['5m'] = aggResults5[i];
        acc[coin]['10m'] = aggResults10[i];
        acc[coin]['60m'] = aggResults60[i];
        return acc
      }, {})

      setGraphData(newGraphData);
    //   setTradeData(newTradeData);
      console.log(newAggData)
      setAggData(newAggData);
    } catch (error) {
      console.error("Error fetching data", error);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Fetch data every 30 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <h1>Crypto Dashboard</h1>
    <div className="dashboard">
      {/* <div className="app-layout" > */}

        {coins.map((coin) => (
            <div key={coin}  className="coin-section">
                <h2>{coin}</h2>
                <GraphComponent data={graphData[coin]} />
                <div className="aggregated-trades">
                    <AggregatedTrades productId={coin} aggData={aggData} />
                </div>
            </div>
        ))}
    </div>
    </>
  );
};

export default App;
