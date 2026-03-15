import React from "react";
import ReactDOM from "react-dom/client";

import logoUrl from "@repo-assets/aegiscore-logo.svg";

import App from "@/app/App";
import "@/styles/index.css";

function upsertHeadLink(rel: string, href: string) {
  let element = document.head.querySelector<HTMLLinkElement>(`link[rel="${rel}"]`);

  if (!element) {
    element = document.createElement("link");
    element.rel = rel;
    document.head.appendChild(element);
  }

  element.href = href;
}

function upsertHeadMeta(name: string, content: string) {
  let element = document.head.querySelector<HTMLMetaElement>(`meta[name="${name}"]`);

  if (!element) {
    element = document.createElement("meta");
    element.name = name;
    document.head.appendChild(element);
  }

  element.content = content;
}

document.title = "AegisCore";
upsertHeadLink("icon", logoUrl);
upsertHeadLink("apple-touch-icon", logoUrl);
upsertHeadMeta("theme-color", "#111111");

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
