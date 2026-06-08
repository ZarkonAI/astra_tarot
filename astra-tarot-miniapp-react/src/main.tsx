import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./app/App";
import "./styles/reset.css";
import "./styles/variables.css";
import "./styles/animations.css";
import "./app/app.css";

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
