import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Wi-Fi RSSI Fall Detection System",
    page_icon="🛜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
            background: #ffffff !important;
            color: #030213 !important;
        }
        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0) !important;
        }
        [data-testid="stToolbar"], [data-testid="stDecoration"], footer {
            display: none !important;
        }
        .block-container {
            padding-top: 0.75rem !important;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            padding-bottom: 0 !important;
            max-width: 100% !important;
        }
        iframe {
            background: #ffffff !important;
            border: 0 !important;
        }
\n</style>
    """,
    unsafe_allow_html=True,
)

DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Wi-Fi RSSI Fall Detection System</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
    @import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap");

    :root {
        --font-size: 16px;
        --background: #ffffff;
        --foreground: #030213;
        --card: #ffffff;
        --card-foreground: #030213;
        --primary: #030213;
        --primary-foreground: #ffffff;
        --secondary: #f3f4f6;
        --secondary-foreground: #030213;
        --muted: #ececf0;
        --muted-foreground: #717182;
        --accent: #e9ebef;
        --accent-foreground: #030213;
        --destructive: #d4183d;
        --destructive-foreground: #ffffff;
        --border: rgba(0, 0, 0, 0.1);
        --input-background: #f3f3f5;
        --font-weight-medium: 500;
        --font-weight-normal: 400;
        --radius: 0.625rem;

        --blue: #2563eb;
        --blue-soft: #eff6ff;
        --blue-line: #bfdbfe;
        --green: #16a34a;
        --green-soft: #f0fdf4;
        --green-line: #bbf7d0;
        --red: #d4183d;
        --red-soft: #fff1f2;
        --red-line: #fecdd3;
        --purple: #7c3aed;
        --purple-soft: #f5f3ff;
        --purple-line: #ddd6fe;
        --shadow: 0 1px 2px rgba(16, 24, 40, 0.04), 0 8px 24px rgba(16, 24, 40, 0.04);
    }

    * { box-sizing: border-box; }

    html, body {
        margin: 0;
        width: 100%;
        min-height: 100%;
        background: var(--background);
        color: var(--foreground);
        font-family: "Inter", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
        font-size: 13px;
        font-weight: var(--font-weight-normal);
        line-height: 1.45;
        letter-spacing: -0.006em;
        text-rendering: geometricPrecision;
    }

    .dashboard {
        width: 100%;
        max-width: 1500px;
        margin: 0 auto;
        padding: 12px 12px 56px;
        background: var(--background);
    }

    .card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
    }

    .header-card {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 22px;
        padding: 26px 28px;
        margin-bottom: 18px;
    }


    .header-brand {
        display: flex;
        align-items: center;
        gap: 14px;
        min-width: 0;
    }

    .brand-symbol {
        width: auto;
        height: auto;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex: 0 0 auto;
        background: transparent;
        border: 0;
        box-shadow: none;
        border-radius: 0;
        font-size: 2.25rem;
        line-height: 1;
    }

    .brand-text {
        min-width: 0;
    }

    .header-title {
        margin: 0;
        color: var(--foreground);
        font-size: clamp(1.85rem, 3vw, 2.45rem);
        line-height: 1.08;
        font-weight: 600;
        letter-spacing: -0.035em;
    }

    .header-subtitle {
        margin: 10px 0 0;
        color: var(--muted-foreground);
        font-size: clamp(0.95rem, 1.2vw, 1.08rem);
        line-height: 1.45;
        font-weight: 400;
    }

    .status-grid {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 8px;
        flex-wrap: wrap;
        min-width: 0;
    }

    .status-card {
        min-height: 38px;
        padding: 8px 12px;
        border-radius: 0.5rem;
        border: 1px solid var(--border);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        white-space: nowrap;
        box-shadow: none;
    }

    .status-icon {
        width: 17px;
        height: 17px;
        border-radius: 999px;
        display: inline-grid;
        place-items: center;
        flex: 0 0 auto;
        font-size: 0.62rem;
        line-height: 1;
        font-weight: 500;
    }

    .status-value {
        color: inherit;
        font-size: 0.78rem;
        line-height: 1;
        font-weight: 500;
        letter-spacing: -0.01em;
    }

    .status-connected {
        color: #047857;
        background: var(--green-soft);
        border-color: var(--green-line);
    }

    .status-connected .status-icon {
        color: #047857;
        background: #dcfce7;
        border: 1px solid #86efac;
    }

    .status-disconnected {
        color: var(--red);
        background: var(--red-soft);
        border-color: var(--red-line);
    }

    .status-disconnected .status-icon {
        color: var(--red);
        background: #ffe4e6;
        border: 1px solid #fda4af;
    }

    .status-model {
        color: #1d4ed8;
        background: var(--blue-soft);
        border-color: var(--blue-line);
    }

    .status-model .status-icon {
        color: #1d4ed8;
        background: #dbeafe;
        border: 1px solid #93c5fd;
        border-radius: 0.25rem;
    }

    .status-time {
        color: #475569;
        background: #f8fafc;
        border-color: #e2e8f0;
    }

    .status-time .status-icon {
        color: #475569;
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
    }

    .section-title {
        margin: 0 0 13px;
        color: var(--foreground);
        font-size: 0.98rem;
        line-height: 1.2;
        font-weight: var(--font-weight-medium);
        letter-spacing: -0.01em;
    }

    .first-row {
        display: grid;
        grid-template-columns: minmax(0, 0.82fr) minmax(0, 1.82fr) minmax(0, 0.96fr);
        grid-auto-rows: 430px;
        gap: 14px;
        margin-bottom: 14px;
        align-items: stretch;
    }

    .second-row {
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
        gap: 14px;
        margin-bottom: 14px;
    }

    .panel {
        padding: 16px;
        min-width: 0;
    }

    label {
        display: block;
        margin-bottom: 6px;
        color: #52637a;
        font-size: 0.73rem;
        font-weight: 400;
    }

    input[type="text"] {
        width: 100%;
        border: 1px solid #d8dee8;
        border-radius: 0.5rem;
        padding: 9px 10px;
        color: var(--foreground);
        background: #ffffff;
        font-size: 0.8rem;
        font-weight: 400;
        outline: none;
    }

    input[type="text"]:focus {
        border-color: #93c5fd;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.09);
    }

    .button {
        width: 100%;
        margin-top: 10px;
        border-radius: 0.5rem;
        padding: 9px 11px;
        font-size: 0.76rem;
        line-height: 1.25;
        font-weight: 500;
        cursor: pointer;
        transition: transform 0.12s ease, opacity 0.12s ease, background 0.12s ease, border-color 0.12s ease;
    }

    .button:active { transform: scale(0.99); }

    .button-primary {
        border: 1px solid var(--blue);
        background: var(--blue);
        color: white;
    }

    .button-primary:hover { background: #1d4ed8; }

    .button-secondary {
        border: 1px solid var(--blue-line);
        background: #ffffff;
        color: var(--blue);
    }

    .button-secondary:hover { background: var(--blue-soft); }

    .button-danger-lite {
        width: auto;
        margin: 0;
        border: 1px solid transparent;
        background: transparent;
        color: var(--red);
        padding: 6px 8px;
        font-size: 0.72rem;
        font-weight: 500;
    }

    .button-danger-lite:hover {
        border-color: var(--red-line);
        background: var(--red-soft);
    }

    .button:disabled {
        opacity: 0.55;
        cursor: not-allowed;
    }

    .divider {
        height: 1px;
        background: #f1f5f9;
        margin: 18px 0;
    }

    .upload-box {
        position: relative;
        min-height: 104px;
        display: grid;
        place-items: center;
        padding: 14px;
        overflow: hidden;
        border: 1px dashed #cbd5e1;
        border-radius: 0.5rem;
        background: #fcfdff;
        color: var(--muted-foreground);
        text-align: center;
        cursor: pointer;
    }

    .upload-box:hover {
        border-color: #93c5fd;
        background: #f8fbff;
    }

    .upload-box input {
        position: absolute;
        inset: 0;
        opacity: 0;
        cursor: pointer;
    }

    .upload-icon {
        margin-bottom: 5px;
        color: #94a3b8;
        font-size: 1.2rem;
        line-height: 1;
        font-weight: 400;
    }

    .upload-main {
        color: var(--foreground);
        font-size: 0.78rem;
        font-weight: 500;
    }

    .upload-sub {
        margin-top: 3px;
        color: var(--muted-foreground);
        font-size: 0.68rem;
        font-weight: 400;
    }

    .helper-text {
        margin-top: 7px;
        color: var(--muted-foreground);
        font-size: 0.72rem;
        font-weight: 400;
        word-break: break-word;
    }

    .input-panel, .signal-card, .result-card {
        height: 430px;
        min-height: 430px;
        max-height: 430px;
    }

    .result-card {
        overflow: hidden;
        padding-bottom: 10px;
    }

    .signal-card {
        display: flex;
        flex-direction: column;
    }

    .chart-wrap {
        flex: 1 1 auto;
        height: 100%;
        min-height: 0;
        padding: 6px;
        position: relative;
        border: 1px solid #f1f5f9;
        border-radius: 0.5rem;
        background: white;
    }

    .chart-wrap canvas {
        width: 100% !important;
        height: 100% !important;
    }

    .placeholder {
        height: 100%;
        min-height: 0;
        display: grid;
        place-items: center;
        padding: 18px;
        border: 1px dashed #d8dee8;
        border-radius: 0.5rem;
        background: #fcfdff;
        color: var(--muted-foreground);
        text-align: center;
        font-size: 0.78rem;
        font-weight: 400;
    }

    .current-file {
        margin: -4px 0 12px;
        color: var(--muted-foreground);
        font-size: 0.72rem;
        font-weight: 400;
    }

    .result-box {
        margin-bottom: 7px;
        padding: 20px 22px;
        min-height: 88px;
        border: 1.7px solid;
        border-radius: 0.82rem;
        display: flex;
        align-items: center;
        gap: 14px;
        font-size: 1.28rem;
        font-weight: 800;
        letter-spacing: 0.006em;
        transform-origin: center;
        animation: breatheResult 1.85s ease-in-out infinite;
        will-change: transform, box-shadow;
    }

    .result-box span:first-child {
        font-size: 1.26rem;
        line-height: 1;
    }

    .result-box span:last-child {
        line-height: 1.08;
    }

    .result-box span:first-child {
        font-size: 1.05rem;
        line-height: 1;
    }

    .fall-box {
        color: var(--red);
        background: var(--red-soft);
        border-color: #fda4af;
        --breathe-shadow: rgba(212, 24, 61, 0.16);
    }

    .normal-box {
        color: var(--green);
        background: var(--green-soft);
        border-color: #86efac;
        --breathe-shadow: rgba(22, 163, 74, 0.14);
    }

    @keyframes breatheResult {
        0%, 100% {
            transform: scale(1);
            box-shadow: 0 0 0 0 rgba(0, 0, 0, 0);
        }
        50% {
            transform: scale(1.014);
            box-shadow: 0 0 0 6px var(--breathe-shadow);
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .result-box { animation: none; }
    }

    .invalid-box {
        align-items: flex-start;
        flex-direction: column;
        gap: 4px;
        color: #475569;
        background: #f8fafc;
        border-color: #d8dee8;
        letter-spacing: 0;
    }

    .invalid-box strong {
        color: var(--foreground);
        font-weight: 500;
    }

    .metric-list {
        display: grid;
        gap: 3px;
    }

    .result-context {
        margin: -2px 0 6px;
        color: #475569;
        font-size: 0.65rem;
        line-height: 1.20;
    }

    .confidence-card {
        background: #f8fafc;
        border-radius: 0.54rem;
        padding: 5px 10px;
        margin-bottom: 42px;
        border: 1px solid #eef2f7;
    }

    .confidence-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        color: #1f3454;
        font-size: 0.70rem;
        margin-bottom: 3px;
    }

    .confidence-value {
        color: #030213;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .progress-track {
        height: 6px;
        border-radius: 999px;
        background: #e5e7eb;
        overflow: hidden;
    }

    .progress-fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.35s ease;
    }

    .progress-fall { background: #ff2d55; }
    .progress-nonfall { background: #16a34a; }

    .metric-row {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 10px;
        padding-bottom: 5px;
        border-bottom: 1px solid #f1f5f9;
        font-size: 0.70rem;
    }

    .metric-row:last-child { border-bottom: none; }

    .metric-label {
        color: var(--muted-foreground);
        font-weight: 400;
    }

    .metric-value {
        color: var(--foreground);
        font-weight: 500;
        text-align: right;
    }

    .alert-note {
        margin-top: 5px;
        padding: 5px 10px;
        border: 1px solid;
        border-radius: 0.48rem;
        font-size: 0.68rem;
        font-weight: 600;
    }

    .alert-note small {
        display: block;
        margin-top: 1px;
        font-size: 0.58rem;
        font-weight: 400;
    }

    .alert-note.red {
        color: #be123c;
        background: #ffe4e6;
        border-color: #fb7185;
    }

    .alert-note.green {
        color: #047857;
        background: #ecfdf5;
        border-color: #86efac;
    }

    .message {
        margin-top: 10px;
        padding: 9px 10px;
        border-radius: 0.5rem;
        font-size: 0.74rem;
        font-weight: 400;
    }

    .message.error {
        color: var(--red);
        background: var(--red-soft);
        border: 1px solid var(--red-line);
    }

    .message.info {
        color: var(--blue);
        background: var(--blue-soft);
        border: 1px solid var(--blue-line);
    }

    .flow-horizontal {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        flex-wrap: wrap;
        padding: 20px 4px 6px;
    }

    .flow-step {
        min-width: 82px;
        max-width: 106px;
        display: grid;
        justify-items: center;
        gap: 8px;
        text-align: center;
    }

    .flow-icon {
        width: 56px;
        height: 56px;
        display: grid;
        place-items: center;
        border-radius: 0.875rem;
        border: 1px solid transparent;
    }

    .flow-icon svg {
        width: 28px;
        height: 28px;
        stroke-width: 2;
    }

    .flow-icon.file {
        color: #2563eb;
        background: #dbeafe;
        border-color: #bfdbfe;
    }

    .flow-icon.signal {
        color: #7c3aed;
        background: #f3e8ff;
        border-color: #e9d5ff;
    }

    .flow-icon.transform {
        color: #16a34a;
        background: #dcfce7;
        border-color: #bbf7d0;
    }

    .flow-icon.mtff {
        color: #0891b2;
        background: #cffafe;
        border-color: #a5f3fc;
    }

    .flow-icon.model {
        color: #4f46e5;
        background: #e0e7ff;
        border-color: #c7d2fe;
    }

    .flow-icon.output {
        color: var(--red);
        background: #fee2e2;
        border-color: #fecaca;
    }

    .flow-label {
        color: #334155;
        font-size: 0.74rem;
        font-weight: 400;
        line-height: 1.22;
    }

    .flow-arrow {
        color: #94a3b8;
        font-size: 1.05rem;
        font-weight: 400;
        line-height: 1;
        margin-top: -20px;
    }

    .flow-vertical { display: none; }

    .info-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
    }

    .info-item {
        min-width: 0;
        padding: 11px 12px;
        border: 1px solid #eef2f7;
        border-radius: 0.5rem;
        background: #f8fafc;
        box-shadow: none;
    }

    .info-label {
        margin-bottom: 5px;
        color: #52637a;
        font-size: 0.68rem;
        font-weight: 400;
    }

    .info-value {
        color: var(--foreground);
        font-size: 0.78rem;
        line-height: 1.3;
        font-weight: 500;
        word-break: break-word;
    }

    .info-value.secondary {
        color: #7b8da8;
        font-size: 0.75rem;
        font-weight: 400;
    }

    .history-card {
        padding: 16px;
        margin-bottom: 20px;
    }

    .history-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 12px;
    }

    .history-actions {
        display: flex;
        justify-content: flex-end;
        gap: 7px;
        flex-wrap: wrap;
    }

    .history-actions .button {
        width: auto;
        margin: 0;
        padding: 6px 8px;
        font-size: 0.7rem;
    }


    .delete-record-btn {
        width: 28px;
        height: 28px;
        margin: 0;
        padding: 0;
        border: 1px solid transparent;
        border-radius: 8px;
        background: transparent;
        color: var(--red);
        display: inline-grid;
        place-items: center;
        cursor: pointer;
        transition: background 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
    }

    .delete-record-btn:hover {
        background: var(--red-soft);
        border-color: var(--red-line);
    }

    .delete-record-btn:active {
        transform: scale(0.96);
    }

    .delete-record-btn svg {
        width: 15px;
        height: 15px;
        stroke-width: 2;
    }

    .table-wrap {
        width: 100%;
        overflow-x: auto;
        border: 1px solid #eef2f7;
        border-radius: 0.5rem;
    }

    table {
        width: 100%;
        min-width: 1000px;
        border-collapse: collapse;
        background: white;
    }

    th, td {
        padding: 10px 11px;
        border-bottom: 1px solid #eef2f7;
        text-align: left;
        vertical-align: middle;
        white-space: nowrap;
        font-size: 0.7rem;
        font-weight: 400;
    }

    th {
        color: #64748b;
        background: #fbfdff;
        font-size: 0.62rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.035em;
    }

    tr:last-child td { border-bottom: 0; }

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 7px;
        border-radius: 999px;
        border: 1px solid transparent;
        font-size: 0.64rem;
        font-weight: 500;
    }

    .badge-fall, .badge-alert {
        color: var(--red);
        background: var(--red-soft);
        border-color: var(--red-line);
    }

    .badge-normal, .badge-low {
        color: var(--green);
        background: var(--green-soft);
        border-color: var(--green-line);
    }

    .badge-high {
        color: var(--red);
        background: var(--red-soft);
        border-color: var(--red-line);
    }

    .badge-manual, .badge-live {
        color: var(--purple);
        background: var(--purple-soft);
        border-color: var(--purple-line);
    }

    .tiny-loader {
        display: inline-block;
        width: 10px;
        height: 10px;
        margin-right: 5px;
        border: 2px solid rgba(37, 99, 235, 0.22);
        border-top-color: var(--blue);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        vertical-align: -2px;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    @media (max-width: 900px) {
        .header-card {
            align-items: flex-start;
            flex-direction: column;
        }

        .status-grid {
            width: 100%;
            justify-content: flex-start;
        }
    }

    @media (max-width: 768px) {
        .dashboard { padding: 10px; }

        .header-card, .panel, .history-card { padding: 14px; }

        .brand-symbol {
            width: auto;
            height: auto;
            border-radius: 0;
            font-size: 1.75rem;
        }

        .header-title {
            font-size: clamp(1.55rem, 7vw, 2rem);
        }

        .header-subtitle {
            font-size: 0.84rem;
        }

        .status-grid {
            display: grid;
            grid-template-columns: 1fr;
        }

        .status-card {
            width: 100%;
            justify-content: flex-start;
        }

        .first-row {
            grid-template-columns: 1fr;
            gap: 12px;
            margin-bottom: 12px;
        }

        .input-panel { order: 1; }
        .result-card { order: 2; }
        .signal-card { order: 3; }

        .second-row {
            grid-template-columns: 1fr;
            gap: 12px;
            margin-bottom: 12px;
        }

        .button, .history-actions .button { width: 100%; }

        .history-header {
            align-items: stretch;
            flex-direction: column;
        }

        .history-actions {
            width: 100%;
            flex-direction: column;
        }

        .flow-horizontal { display: none; }

        .flow-vertical {
            display: grid;
            gap: 8px;
        }

        .vertical-step {
            display: flex;
            align-items: center;
            gap: 9px;
            padding: 9px 10px;
            border: 1px solid #eef2f7;
            border-radius: 0.5rem;
            background: #fcfdff;
            font-size: 0.78rem;
        }

        .vertical-step .flow-icon {
            width: 34px;
            height: 34px;
            border-radius: 0.65rem;
            flex: 0 0 auto;
        }

        .vertical-step .flow-icon svg {
            width: 19px;
            height: 19px;
        }

        .step-number {
            width: 24px;
            height: 24px;
            display: grid;
            place-items: center;
            flex: 0 0 auto;
            border-radius: 0.45rem;
            background: var(--blue-soft);
            color: var(--blue);
            font-size: 0.72rem;
            font-weight: 500;
        }

        .info-grid { grid-template-columns: 1fr; }
        .input-panel, .signal-card, .result-card {
            height: auto;
            min-height: 0;
        }
        .chart-wrap { height: 245px; min-height: 245px; }
        .placeholder { min-height: 0; }
        table { min-width: 880px; }
        th, td { padding: 9px 10px; }
    }


    /* Fixed Recent Official Test Checks card: 5 visible logs, scroll after that */
    .history-card {
        height: 300px;
        min-height: 300px;
        max-height: 300px;
        overflow: hidden;
        padding: 14px 16px;
        margin-bottom: 42px;
    }

    .history-header {
        margin-bottom: 8px;
    }

    #historyContainer.table-wrap {
        width: 100%;
        max-height: 212px;
        overflow-y: auto;
        overflow-x: auto;
        border: 1px solid #eef2f7;
        border-radius: 0.5rem;
    }

    #historyContainer thead th {
        position: sticky;
        top: 0;
        z-index: 3;
        background: #fbfdff;
    }

    #historyContainer th,
    #historyContainer td {
        padding: 8px 10px;
        line-height: 1.18;
    }


    /* FINAL OFFICIAL RESULT CARD POLISH: bigger animated top alert, fixed inside 430px card */
    .first-row {
        grid-auto-rows: 430px !important;
        align-items: stretch !important;
    }

    .input-panel, .signal-card, .result-card {
        height: 430px !important;
        min-height: 430px !important;
        max-height: 430px !important;
    }

    .result-card {
        overflow: hidden !important;
        padding: 14px 16px 10px !important;
        display: flex !important;
        flex-direction: column !important;
    }

    .result-card .section-title {
        margin-bottom: 8px !important;
        flex: 0 0 auto !important;
    }

    .current-file {
        margin: -1px 0 8px !important;
        font-size: 0.68rem !important;
        flex: 0 0 auto !important;
    }

    #resultContent {
        flex: 1 1 auto !important;
        min-height: 0 !important;
        display: flex !important;
        flex-direction: column !important;
        overflow: hidden !important;
    }

    .result-box {
        min-height: 112px !important;
        margin: 0 0 6px !important;
        padding: 24px 24px !important;
        border-width: 2px !important;
        border-radius: 0.9rem !important;
        display: flex !important;
        align-items: center !important;
        gap: 16px !important;
        font-size: 1.42rem !important;
        line-height: 1.08 !important;
        font-weight: 800 !important;
        letter-spacing: 0.006em !important;
        flex: 0 0 auto !important;
        transform-origin: center !important;
        animation: breatheResult 1.85s ease-in-out infinite !important;
        will-change: transform, box-shadow !important;
    }

    .result-box span:first-child {
        font-size: 1.36rem !important;
        line-height: 1 !important;
    }

    .result-box span:last-child {
        line-height: 1.08 !important;
    }

    .fall-box {
        --breathe-shadow: rgba(212, 24, 61, 0.18) !important;
    }

    .normal-box {
        --breathe-shadow: rgba(22, 163, 74, 0.16) !important;
    }

    @keyframes breatheResult {
        0%, 100% {
            transform: scale(1);
            box-shadow: 0 0 0 0 rgba(0, 0, 0, 0);
        }
        50% {
            transform: scale(1.012);
            box-shadow: 0 0 0 6px var(--breathe-shadow);
        }
    }

    .result-context {
        margin: 0 0 5px !important;
        font-size: 0.60rem !important;
        line-height: 1.12 !important;
        flex: 0 0 auto !important;
    }

    .confidence-card {
        padding: 4px 9px !important;
        margin: 0 0 5px !important;
        border-radius: 0.50rem !important;
        flex: 0 0 auto !important;
    }

    .confidence-head {
        font-size: 0.66rem !important;
        margin-bottom: 3px !important;
        gap: 8px !important;
    }

    .confidence-value {
        font-size: 0.76rem !important;
    }

    .progress-track {
        height: 5px !important;
    }

    .metric-list {
        gap: 2px !important;
        flex: 0 0 auto !important;
    }

    .metric-row {
        padding-bottom: 3px !important;
        font-size: 0.64rem !important;
    }

    .alert-note {
        margin-top: 13px !important;
        padding: 5px 9px !important;
        border-radius: 0.46rem !important;
        font-size: 0.64rem !important;
        flex: 0 0 auto !important;
    }

    .alert-note small {
        margin-top: 1px !important;
        font-size: 0.55rem !important;
    }



    /* FINAL RESULT CARD BALANCE PATCH: avoid breathing cut, move context down, enlarge confidence and lower alert */
    .result-card {
        overflow: hidden !important;
        padding: 14px 16px 10px !important;
        display: flex !important;
        flex-direction: column !important;
    }

    #resultContent {
        flex: 1 1 auto !important;
        min-height: 0 !important;
        display: flex !important;
        flex-direction: column !important;
        overflow: hidden !important;
    }

    .result-box {
        width: calc(100% - 72px) !important;
        min-height: 75px !important;
        margin: 8px auto 12px !important;
        padding: 15px 22px !important;
        border-width: 2px !important;
        border-radius: 0.86rem !important;
        display: flex !important;
        align-items: center !important;
        gap: 15px !important;
        font-size: 1.34rem !important;
        line-height: 1.08 !important;
        font-weight: 800 !important;
        letter-spacing: 0.006em !important;
        flex: 0 0 auto !important;
        transform-origin: center !important;
        animation: breatheResult 1.85s ease-in-out infinite !important;
        will-change: transform, box-shadow !important;
    }

    .result-box span:first-child {
        font-size: 1.26rem !important;
        line-height: 1 !important;
    }

    .result-box span:last-child {
        line-height: 1.08 !important;
    }

    @keyframes breatheResult {
        0%, 100% {
            transform: scale(1);
            box-shadow: 0 0 0 0 rgba(0, 0, 0, 0);
        }
        50% {
            transform: scale(1.006);
            box-shadow: 0 0 0 4px var(--breathe-shadow);
        }
    }

    .result-context {
        margin: 9px 0 9px !important;
        font-size: 0.64rem !important;
        line-height: 1.18 !important;
        flex: 0 0 auto !important;
    }

    .confidence-card {
        padding: 7px 11px !important;
        margin: 0 0 7px !important;
        border-radius: 0.58rem !important;
        flex: 0 0 auto !important;
    }

    .confidence-head {
        font-size: 0.72rem !important;
        margin-bottom: 5px !important;
        gap: 9px !important;
    }

    .confidence-value {
        font-size: 0.90rem !important;
        font-weight: 700 !important;
    }

    .progress-track {
        height: 7px !important;
    }

    .metric-list {
        gap: 3px !important;
        flex: 0 0 auto !important;
    }

    .metric-row {
        padding-bottom: 4px !important;
        font-size: 0.68rem !important;
    }

    .alert-note {
        min-height: 50px !important;
        margin-top: 13px !important;
        padding: 8px 11px !important;
        border-radius: 0.52rem !important;
        font-size: 0.72rem !important;
        flex: 0 0 auto !important;
    }

    .alert-note small {
        margin-top: 3px !important;
        font-size: 0.62rem !important;
    }



    /* FINAL RESPONSIVE VIEW PATCH: result alert + iframe auto height */
    .dashboard {
        padding-bottom: 10px !important;
    }

    .history-card {
        margin-bottom: 0 !important;
    }

    .result-box {
        width: min(calc(100% - 32px), 720px) !important;
        max-width: 100% !important;
        min-height: 75px !important;
        margin: 8px auto 12px !important;
        padding: clamp(10px, 1.45vw, 15px) clamp(14px, 2vw, 22px) !important;
        gap: clamp(8px, 1.25vw, 15px) !important;
        font-size: clamp(0.92rem, 1.35vw, 1.34rem) !important;
        line-height: 1.08 !important;
        white-space: normal !important;
        text-align: left !important;
        justify-content: center !important;
        overflow: visible !important;
    }

    .result-box span:first-child {
        flex: 0 0 auto !important;
        font-size: clamp(0.95rem, 1.3vw, 1.26rem) !important;
    }

    .result-box span:last-child {
        min-width: 0 !important;
        max-width: 100% !important;
        white-space: normal !important;
        overflow-wrap: break-word !important;
        word-break: normal !important;
    }

    @media (max-width: 1100px) {
        .first-row {
            grid-template-columns: 1fr !important;
            grid-auto-rows: auto !important;
        }

        .input-panel,
        .signal-card,
        .result-card {
            height: auto !important;
            min-height: 0 !important;
            max-height: none !important;
        }

        .result-card {
            overflow: visible !important;
        }

        #resultContent {
            overflow: visible !important;
        }

        .chart-wrap {
            height: 360px !important;
            min-height: 360px !important;
        }

        .result-box {
            width: min(calc(100% - 28px), 720px) !important;
            font-size: clamp(1.05rem, 3.6vw, 1.34rem) !important;
        }
    }

    @media (max-width: 768px) {
        .dashboard {
            padding: 10px 10px 10px !important;
        }

        .first-row,
        .second-row {
            grid-template-columns: 1fr !important;
            gap: 12px !important;
        }

        .input-panel,
        .signal-card,
        .result-card {
            height: auto !important;
            min-height: 0 !important;
            max-height: none !important;
        }

        .result-card {
            overflow: visible !important;
            padding-bottom: 14px !important;
        }

        #resultContent {
            overflow: visible !important;
        }

        .result-box {
            width: calc(100% - 24px) !important;
            min-height: 68px !important;
            padding: 12px 14px !important;
            gap: 10px !important;
            font-size: clamp(0.98rem, 5.2vw, 1.22rem) !important;
            border-radius: 0.78rem !important;
        }

        .result-box span:first-child {
            font-size: clamp(0.95rem, 5vw, 1.14rem) !important;
        }

        .chart-wrap {
            height: 320px !important;
            min-height: 320px !important;
        }

        .history-card {
            height: 300px !important;
            min-height: 300px !important;
            max-height: 300px !important;
            margin-bottom: 0 !important;
        }
    }

    @media (max-width: 420px) {
        .result-box {
            width: calc(100% - 18px) !important;
            min-height: 64px !important;
            padding: 10px 12px !important;
            gap: 8px !important;
            font-size: clamp(0.90rem, 5.6vw, 1.05rem) !important;
        }
    }



    /* EDITED INPUT PANEL ONLY: auto-upload + saved testing data picker + desktop-fit warnings */
    .saved-data-box {
        margin-top: 12px;
        padding: 10px;
        border: 1px solid #eef2f7;
        border-radius: 0.58rem;
        background: #fbfdff;
    }

    .saved-data-title {
        color: var(--foreground);
        font-size: 0.76rem;
        font-weight: 600;
        margin-bottom: 3px;
    }

    .saved-data-sub {
        color: var(--muted-foreground);
        font-size: 0.66rem;
        line-height: 1.25;
        margin-bottom: 8px;
    }

    .sample-select {
        width: 100%;
        min-width: 0;
        border: 1px solid #d8dee8;
        border-radius: 0.50rem;
        background: #ffffff;
        color: var(--foreground);
        padding: 8px 9px;
        font-size: 0.70rem;
        outline: none;
    }

    .sample-select:focus {
        border-color: #93c5fd;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.09);
    }

    .sample-button {
        margin-top: 8px !important;
        padding: 8px 10px !important;
        font-size: 0.70rem !important;
    }

    @media (min-width: 1101px) {
        .input-panel {
            overflow-y: auto !important;
            overflow-x: hidden !important;
            padding: 14px !important;
        }

        .input-panel .section-title {
            margin-bottom: 8px !important;
        }

        .upload-only-note {
            margin: 0 0 8px !important;
            font-size: 0.65rem !important;
            line-height: 1.22 !important;
        }

        .input-panel label {
            margin-bottom: 4px !important;
            font-size: 0.67rem !important;
        }

        .upload-box {
            min-height: 82px !important;
            padding: 10px !important;
        }

        .upload-main {
            font-size: 0.73rem !important;
        }

        .upload-sub {
            font-size: 0.62rem !important;
        }

        #selectedFileName {
            min-height: 16px !important;
            margin-top: 5px !important;
            font-size: 0.64rem !important;
            line-height: 1.18 !important;
        }

        #uploadMessage,
        #sampleMessage {
            min-height: 34px !important;
            max-height: 34px !important;
            overflow: hidden !important;
            margin: 0 !important;
            display: block !important;
        }

        #uploadMessage .message,
        #sampleMessage .message {
            margin-top: 6px !important;
            padding: 7px 8px !important;
            font-size: 0.61rem !important;
            line-height: 1.15 !important;
            border-radius: 0.44rem !important;
        }

        .saved-data-box {
            margin-top: 4px !important;
            padding: 8px !important;
            border-radius: 0.52rem !important;
        }

        .saved-data-title {
            font-size: 0.72rem !important;
            margin-bottom: 2px !important;
        }

        .saved-data-sub {
            font-size: 0.60rem !important;
            line-height: 1.16 !important;
            margin-bottom: 6px !important;
        }

        .sample-select {
            padding: 7px 8px !important;
            font-size: 0.65rem !important;
            min-height: 34px !important;
        }

        .sample-button {
            margin-top: 7px !important;
            padding: 7px 8px !important;
            font-size: 0.65rem !important;
        }
    }

</style>
</head>
<body>
<div class="dashboard">
    <header class="header-card card">
        <div class="header-brand">
            <div class="brand-symbol" aria-hidden="true">🛜</div>
            <div class="brand-text">
                <h1 class="header-title">Wi-Fi RSSI Fall Detection System</h1>
                <p class="header-subtitle">Official nested-CV outer-test result explorer for Wi-Fi RSSI fall detection</p>
            </div>
        </div>
        <div class="status-grid">
            <div id="backendStatusCard" class="status-card status-connected">
                <span id="backendIcon" class="status-icon">✓</span>
                <span id="backendStatus" class="status-value">Checking...</span>
            </div>
            <div class="status-card status-model">
                <span class="status-icon">▣</span>
                <span id="modelStatus" class="status-value">Model: MTFF</span>
            </div>
            <div class="status-card status-time">
                <span class="status-icon">◷</span>
                <span id="lastClassification" class="status-value">Last: Loading...</span>
            </div>
        </div>
    </header>

    <main>
        <section class="first-row">
            <article class="card panel input-panel" id="inputPanel">
                <h2 class="section-title">Input Panel</h2>

                <p class="helper-text upload-only-note">
                    Upload a .mat testing file to check its official nested-CV outer-test result and display the extracted envelope signal.
                </p>

                <label for="fileUpload">Upload .mat File</label>

                <div class="upload-box">
                    <input id="fileUpload" type="file" accept=".mat" onchange="handleFileSelect()" />
                    <div>
                        <div class="upload-icon"></div>
                        <div class="upload-main">Click to browse</div>
                        <div class="upload-sub">Accepted: .mat</div>
                    </div>
                </div>

                <div id="selectedFileName" class="helper-text">No file selected</div>
                <div id="uploadMessage"></div>

                <div class="saved-data-box">
                    <div class="saved-data-title">Saved Testing Data</div>
                    <div class="saved-data-sub">Pick a saved testing file to visualise without manual upload.</div>

                    <select id="sampleDataSelect" class="sample-select" onchange="handleSampleSelect()">
                        <option value="">Loading saved testing data...</option>
                    </select>

                    <button id="sampleBtn" class="button button-secondary sample-button" onclick="loadSelectedSample()">
                        Visualise Selected Testing Data
                    </button>

                    <div id="sampleMessage"></div>
                </div>
            </article>

            <article class="card panel signal-card">
                <h2 class="section-title">Envelope Signal Preview</h2>
                <div id="chartContainer" class="chart-wrap">
                    <div id="signalPlaceholder" class="placeholder">Envelope preview available after selecting a test file</div>
                    <canvas id="rssiChart" style="display:none;"></canvas>
                </div>
            </article>

            <article class="card panel result-card">
                <h2 class="section-title">Official Testing Result</h2>
                <div id="currentFile" class="current-file">Current file: None</div>
                <div id="resultContent">
                    <div class="result-box invalid-box">
                        <strong>No official testing result selected</strong>
                        <span>Please choose an official test file.</span>
                    </div>
                </div>
            </article>
        </section>

        <section class="second-row">
            <article class="card panel">
                <h2 class="section-title">Official Testing Flow</h2>
                <div class="flow-horizontal" aria-label="System processing flow">
                    <div class="flow-step">
                        <div class="flow-icon file">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><ellipse cx="12" cy="5" rx="7" ry="3"></ellipse><path d="M5 5v14c0 1.7 3.1 3 7 3s7-1.3 7-3V5"></path><path d="M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"></path></svg>
                        </div>
                        <div class="flow-label">MATLAB<br>.mat File</div>
                    </div>
                    <div class="flow-arrow">›</div>
                    <div class="flow-step">
                        <div class="flow-icon signal">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 20v-2"></path><path d="M9 20v-6"></path><path d="M13 20V9"></path><path d="M17 20V5"></path><path d="M21 20V3"></path></svg>
                        </div>
                        <div class="flow-label">Envelope<br>Signal</div>
                    </div>
                    <div class="flow-arrow">›</div>
                    <div class="flow-step">
                        <div class="flow-icon transform">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M3 12h4l3-8 4 16 3-8h4"></path></svg>
                        </div>
                        <div class="flow-label">FFT + STFT<br>+ CWT</div>
                    </div>
                    <div class="flow-arrow">›</div>
                    <div class="flow-step">
                        <div class="flow-icon mtff">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M13 2 4 14h7l-1 8 10-13h-7l1-7Z"></path></svg>
                        </div>
                        <div class="flow-label">MTFF</div>
                    </div>
                    <div class="flow-arrow">›</div>
                    <div class="flow-step">
                        <div class="flow-icon model">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><ellipse cx="12" cy="5" rx="7" ry="3"></ellipse><path d="M5 5v14c0 1.7 3.1 3 7 3s7-1.3 7-3V5"></path><path d="M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"></path></svg>
                        </div>
                        <div class="flow-label">Saved Outer-Test<br>Prediction</div>
                    </div>
                    <div class="flow-arrow">›</div>
                    <div class="flow-step">
                        <div class="flow-icon output">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m4 14 5-5 4 4 7-7"></path><path d="M14 6h6v6"></path></svg>
                        </div>
                        <div class="flow-label">Official<br>Result</div>
                    </div>
                </div>
                <div class="flow-vertical">
                    <div class="vertical-step"><span class="flow-icon file"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><ellipse cx="12" cy="5" rx="7" ry="3"></ellipse><path d="M5 5v14c0 1.7 3.1 3 7 3s7-1.3 7-3V5"></path><path d="M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"></path></svg></span><span>MATLAB .mat File</span></div>
                    <div class="vertical-step"><span class="flow-icon signal"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 20v-2"></path><path d="M9 20v-6"></path><path d="M13 20V9"></path><path d="M17 20V5"></path><path d="M21 20V3"></path></svg></span><span>Envelope Signal</span></div>
                    <div class="vertical-step"><span class="flow-icon transform"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M3 12h4l3-8 4 16 3-8h4"></path></svg></span><span>FFT + STFT + CWT</span></div>
                    <div class="vertical-step"><span class="flow-icon mtff"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M13 2 4 14h7l-1 8 10-13h-7l1-7Z"></path></svg></span><span>MTFF</span></div>
                    <div class="vertical-step"><span class="flow-icon model"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><ellipse cx="12" cy="5" rx="7" ry="3"></ellipse><path d="M5 5v14c0 1.7 3.1 3 7 3s7-1.3 7-3V5"></path><path d="M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"></path></svg></span><span>Saved Outer-Test Prediction</span></div>
                    <div class="vertical-step"><span class="flow-icon output"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m4 14 5-5 4 4 7-7"></path><path d="M14 6h6v6"></path></svg></span><span>Official Result</span></div>
                </div>
            </article>

            <article class="card panel">
                <h2 class="section-title">Technical Model Information</h2>
                <div id="modelInfoGrid" class="info-grid">
                    <div class="info-item"><div class="info-label">Model</div><div class="info-value">MTFF (Multi-Transform Feature Fusion)</div></div>
                    <div class="info-item"><div class="info-label">Classifier</div><div class="info-value">LightGBM</div></div>
                    <div class="info-item"><div class="info-label">Feature Method</div><div class="info-value">Multi-Transform Feature Fusion</div></div>
                    <div class="info-item"><div class="info-label">Feature Order</div><div class="info-value">FFT + STFT + CWT</div></div>
                    <div class="info-item"><div class="info-label">Threshold Rule</div><div class="info-value">Inner-CV tuned, specificity ≥ 0.60.</div></div>
                    <div class="info-item"><div class="info-label">Dashboard Mode</div><div class="info-value">Saved official test-result lookup</div></div>
                </div>
            </article>
        </section>

        <section class="history-card card">
            <div class="history-header">
                <h2 class="section-title" style="margin:0;">Recent Official Test Checks</h2>
                <div class="history-actions">
                    <button id="clearAllBtn" class="button button-danger-lite" onclick="clearAllHistory()">Clear All History</button>
                </div>
            </div>
            <div id="historyMessage"></div>
            <div id="historyContainer" class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>File Name</th>
                            <th>Official Result</th>
                            <th>Fall Confidence</th>
                            <th>Risk Level</th>
                            <th>Input Mode</th>
                            <th>Processing Time</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody id="historyBody">
                        <tr><td colspan="9">Loading history...</td></tr>
                    </tbody>
                </table>
            </div>
        </section>
    </main>
</div>

<script>
// Change this only when switching between local FastAPI and Render.
// Local:  const API_BASE_URL = "https://wi-fi-rssi-fall-detection-system.onrender.com";
// Render: const API_BASE_URL = "https://wi-fi-rssi-fall-detection-system.onrender.com";
const API_BASE_URL = "https://wi-fi-rssi-fall-detection-system.onrender.com";

let state = {
    modelInfo: null,
    history: [],
    currentResult: null,
    currentFile: null,
    selectedFile: null,
    sampleFiles: [],
    selectedSamplePath: "",
    chart: null,
    loading: false
};

function friendlyErrorMessage() {
    return "File not found in official nested-CV result list. Please upload a .mat file that exists in the evaluation dataset.";
}

function setMessage(targetId, message, type = "info") {
    const el = document.getElementById(targetId);
    if (!el) return;
    if (!message) {
        el.innerHTML = "";
        return;
    }
    el.innerHTML = `<div class="message ${type}">${message}</div>`;
}

function setLoading(buttonId, isLoading, loadingText = "Loading...") {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    if (isLoading) {
        btn.dataset.originalText = btn.textContent;
        btn.innerHTML = `<span class="tiny-loader"></span>${loadingText}`;
        btn.disabled = true;
    } else {
        btn.textContent = btn.dataset.originalText || btn.textContent;
        btn.disabled = false;
    }
}

async function safeFetch(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
        throw new Error("Request failed");
    }
    const text = await response.text();
    if (!text) return {};
    try {
        return JSON.parse(text);
    } catch {
        return {};
    }
}

function normalizeActivity(value) {
    if (value === undefined || value === null) return "";
    const text = String(value).trim();
    const lower = text.toLowerCase().replace(/_/g, "-");
    if (lower.includes("non-fall") || lower.includes("nonfall") || lower.includes("normal")) return "Non-Fall";
    if (lower.includes("fall")) return "Fall";
    return text;
}

function isFallActivity(activity) {
    return normalizeActivity(activity) === "Fall";
}

function formatPercent(value) {
    if (value === undefined || value === null || value === "") return "—";
    if (typeof value === "string" && value.includes("%")) return value.trim();
    const numeric = Number(value);
    if (Number.isNaN(numeric)) return String(value);
    const percent = Math.max(0, Math.min(100, numeric));
    return `${percent.toFixed(1)}%`;
}

function _toPercentFromProbability(value) {
    if (value === undefined || value === null || value === "") return null;
    if (typeof value === "string") value = value.replace("%", "").trim();
    const numeric = Number(value);
    if (Number.isNaN(numeric)) return null;
    return Math.max(0, Math.min(100, numeric <= 1 ? numeric * 100 : numeric));
}

function _toPercentLiteral(value) {
    if (value === undefined || value === null || value === "") return null;
    if (typeof value === "string") value = value.replace("%", "").trim();
    const numeric = Number(value);
    if (Number.isNaN(numeric)) return null;
    return Math.max(0, Math.min(100, numeric));
}

function _clampPercent(value) {
    return Math.max(0, Math.min(100, Number(value)));
}

function getConfidencePair(data, activity = null) {
    if (!data) return { fallConfidence: null, nonFallConfidence: null };

    // FinalProb/probability/fall_probability is Fall probability.
    // Non-Fall confidence is always 100 - Fall confidence.
    // No label-based flipping is used.
    let fallPercent = _toPercentFromProbability(
        data?.official_final_probability ??
        data?.final_probability ??
        data?.fall_probability ??
        data?.FinalProb ??
        data?.final_prob ??
        data?.probability ??
        data?.display_fall_probability ??
        data?.display_fall_prob ??
        null
    );

    // Percent fields are already percentages, so 0.96 means 0.96%, not 96%.
    if (fallPercent === null) {
        fallPercent = _toPercentLiteral(data?.fall_confidence_percent ?? data?.fall_confidence ?? null);
    }

    if (fallPercent === null) {
        const nonFallPercent = _toPercentLiteral(data?.non_fall_confidence_percent ?? data?.non_fall_confidence ?? null);
        if (nonFallPercent !== null) fallPercent = 100 - nonFallPercent;
    }

    if (fallPercent === null) return { fallConfidence: null, nonFallConfidence: null };

    fallPercent = _clampPercent(fallPercent);
    const nonFallPercent = _clampPercent(100 - fallPercent);
    return { fallConfidence: fallPercent, nonFallConfidence: nonFallPercent };
}

function getFallConfidence(data) {
    return getConfidencePair(data, null).fallConfidence;
}

function getNonFallConfidence(data) {
    return getConfidencePair(data, null).nonFallConfidence;
}

function percentNumber(value) {
    if (value === undefined || value === null || value === "") return 0;
    if (typeof value === "string" && value.includes("%")) value = value.replace("%", "");
    const numeric = Number(value);
    if (Number.isNaN(numeric)) return 0;
    return Math.max(0, Math.min(100, numeric));
}

function formatSeconds(value) {
    if (value === undefined || value === null || value === "") return "—";
    if (typeof value === "string" && value.endsWith("s")) return value;
    const numeric = Number(value);
    if (Number.isNaN(numeric)) return String(value);
    if (numeric < 1) return `${numeric.toFixed(3)}s`;
    return `${numeric.toFixed(2)}s`;
}

function cleanThreshold(value) {
    const fallback = getModelField(["decision_threshold", "threshold"], 0.70);
    const raw = value ?? fallback;
    const numeric = Number(raw);
    if (Number.isNaN(numeric)) return "0.70";
    return numeric.toFixed(2);
}

function formatMalaysiaTimestamp(value) {
    if (!value) return "—";
    const raw = String(value).trim();

    if (!raw.includes("T") && !raw.includes("+") && !raw.endsWith("Z")) {
        const compact = raw.replace(/\.\d+$/, "");
        return compact.length >= 19 ? compact.slice(0, 19) : compact;
    }

    const date = new Date(raw);
    if (!Number.isNaN(date.getTime())) {
        const parts = new Intl.DateTimeFormat("en-CA", {
            timeZone: "Asia/Kuala_Lumpur",
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false
        }).formatToParts(date);

        const get = (type) => parts.find(p => p.type === type)?.value || "";
        return `${get("year")}-${get("month")}-${get("day")} ${get("hour")}:${get("minute")}:${get("second")}`;
    }

    return raw.replace("T", " ").replace(/\+08:00$/, "").replace(/Z$/, "").slice(0, 19);
}

function getRecordTimestamp(record) {
    return record?.timestamp_display || record?.timestamp || "";
}

function getLatestHistoryRecord(records) {
    if (!Array.isArray(records) || records.length === 0) return null;
    let latest = records[0];
    let latestTime = Date.parse(records[0].timestamp || records[0].timestamp_display || "");
    for (const record of records) {
        const parsed = Date.parse(record.timestamp || record.timestamp_display || "");
        if (!Number.isNaN(parsed) && (Number.isNaN(latestTime) || parsed > latestTime)) {
            latest = record;
            latestTime = parsed;
        }
    }
    return latest;
}

function getModelField(keys, fallback) {
    const info = state.modelInfo || {};
    for (const key of keys) {
        if (info[key] !== undefined && info[key] !== null && info[key] !== "") return info[key];
    }
    return fallback;
}

function sanitizeFeatureOrder(value) {
    if (!value) return "FFT + STFT + CWT";
    return String(value)
        .replace(/FFT_128/gi, "FFT")
        .replace(/STFT_128/gi, "STFT")
        .replace(/CWT_128/gi, "CWT")
        .replace(/\s*\+\s*/g, " + ");
}

function renderModelInfo() {
    document.getElementById("modelStatus").textContent = "Official Test: MTFF";

    const thresholdRule = "Inner-CV tuned, specificity ≥ 0.60.";

    const items = [
        ["Model", "MTFF (Multi-Transform Feature Fusion)", ""],
        ["Classifier", getModelField(["classifier", "model_type"], "LightGBM"), ""],
        ["Feature Method", "Multi-Transform Feature Fusion", ""],
        ["Feature Order", sanitizeFeatureOrder(getModelField(["feature_order"], "FFT + STFT + CWT")), ""],
        ["Threshold Rule", thresholdRule, ""],
        ["Dashboard Mode", "Saved official test-result lookup", ""],
    ];

    document.getElementById("modelInfoGrid").innerHTML = items.map(([label, value, secondaryClass]) => `
        <div class="info-item">
            <div class="info-label">${label}</div>
            <div class="info-value ${secondaryClass}">${escapeHtml(value)}</div>
        </div>
    `).join("");
}

function extractPredictionData(data) {
    const payload = data?.result || data?.data || data?.classification || data || {};
    const activity = normalizeActivity(
        payload.prediction_text ??
        payload.classified_activity ??
        payload.activity ??
        payload.classification ??
        payload.label ??
        payload.result ??
        payload.prediction
    );

    if (!activity || (activity !== "Fall" && activity !== "Non-Fall")) {
        return null;
    }

    const confidencePair = getConfidencePair(payload, activity);
    const confidence = confidencePair.fallConfidence;
    const nonFallConfidence = confidencePair.nonFallConfidence;
    const risk = payload.risk_level || (activity === "Fall" ? "High" : "Low");
    const processingTime = (
        payload.processing_time_sec ??
        payload.processing_time ??
        payload.inference_time_sec ??
        payload.elapsed_time_sec ??
        null
    );

    return {
        raw: payload,
        activity,
        confidence,
        nonFallConfidence,
        threshold: payload.decision_threshold ?? payload.threshold ?? null,
        risk,
        processingTime,
        status: payload.status || (activity === "Fall" ? "Alert" : "Normal"),
        alertText: activity === "Fall"
            ? "Official Prediction: Fall — Check actual label/correctness"
            : "Official Prediction: Non-Fall — Check actual label/correctness"
    };
}

function clearClassification(fileName = null) {
    state.currentResult = null;
    state.currentFile = fileName;
    renderResult();
}

function renderResult() {
    const currentFile = state.currentFile || "None";
    document.getElementById("currentFile").textContent = `Current file: ${currentFile}`;

    const container = document.getElementById("resultContent");
    const result = state.currentResult;

    if (!result) {
        container.innerHTML = `
            <div class="result-box invalid-box">
                <strong>No official testing result selected</strong>
                <span>Please choose another official test file.</span>
            </div>
        `;
        return;
    }

    const fall = result.activity === "Fall";
    const boxClass = fall ? "fall-box" : "normal-box";
    const title = fall ? "FALL DETECTED" : "NON-FALL DETECTED";
    const alertClass = fall ? "red" : "green";
    const raw = result.raw || {};
    const actualLabel = raw.actual_label_text || raw.actual_label || "—";
    const actualEvent = raw.actual_event || raw.event || "—";
    const outerFold = raw.outer_fold ?? raw.OuterFold ?? "—";
    const correctText = raw.correct === true ? "Correct" : (raw.correct === false ? "Wrong" : "—");
    const correctnessClass = raw.correct === true ? "green" : (raw.correct === false ? "red" : "");
    const fallPercent = percentNumber(result.confidence);
    const nonFallPercent = percentNumber(result.nonFallConfidence);

    const alertTitle = fall ? "⊗ Alert Triggered" : "⊙ No Fall Alert";
    const alertMessage = fall
        ? "Immediate attention required"
        : "No immediate fall alert required";

    container.innerHTML = `
        <div class="result-box ${boxClass}">
            <span>${fall ? "⊗" : "⊙"}</span>
            <span>${title}</span>
        </div>

        <div class="result-context">
            Actual: <strong>${escapeHtml(actualLabel)}</strong> (${escapeHtml(actualEvent)})<br>
            Outer fold: <strong>${escapeHtml(outerFold)}</strong> · Correctness: <strong class="${correctnessClass}">${escapeHtml(correctText)}</strong><br>
            Official CV role: <strong>${escapeHtml(raw.official_role_display || (outerFold !== "—" ? `Outer Test (Fold ${outerFold})` : "Outer Test"))}</strong>
        </div>

        <div class="confidence-card">
            <div class="confidence-head">
                <span>Fall Confidence</span>
                <span class="confidence-value">${formatPercent(result.confidence)}</span>
            </div>
            <div class="progress-track"><div class="progress-fill progress-fall" style="width:${fallPercent}%;"></div></div>
        </div>

        <div class="confidence-card">
            <div class="confidence-head">
                <span>Non-Fall Confidence</span>
                <span class="confidence-value">${formatPercent(result.nonFallConfidence)}</span>
            </div>
            <div class="progress-track"><div class="progress-fill progress-nonfall" style="width:${nonFallPercent}%;"></div></div>
        </div>

        <div class="metric-list">
            <div class="metric-row">
                <span class="metric-label">Threshold Rule</span>
                <span class="metric-value">${cleanThreshold(result.threshold)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Lookup Time</span>
                <span class="metric-value">${formatSeconds(result.processingTime)}</span>
            </div>
        </div>

        <div class="alert-note ${alertClass}">
            ${alertTitle}
            <small>${alertMessage}</small>
        </div>
    `;
}

function buildSampleSignal(activity = "Fall") {
    const values = [];
    for (let i = 0; i < 110; i++) {
        const base = -38 + Math.sin(i / 5) * 3.5 + Math.sin(i / 13) * 1.4;
        const eventDip = activity === "Fall" ? -35 * Math.exp(-Math.pow((i - 56) / 12, 2)) : -6 * Math.exp(-Math.pow((i - 56) / 18, 2));
        values.push(Number((base + eventDip).toFixed(2)));
    }
    return values;
}

function extractSignal(data) {
    const payload = data?.result || data?.data || data?.classification || data || {};

    const previewObjects = [
        payload.signal_preview,
        payload.envelope_preview,
        payload.plot_data?.envelope,
        payload.chart?.envelope,
        data?.signal_preview,
        data?.envelope_preview
    ];

    for (const preview of previewObjects) {
        if (preview && typeof preview === "object") {
            const xRaw = preview.x || preview.t || preview.time || preview.envelope_time || preview.time_sec || [];
            const yRaw = preview.y || preview.values || preview.amplitude || preview.signal || preview.envelope_signal || [];
            if (Array.isArray(yRaw) && yRaw.length > 0) {
                const yValues = yRaw.map(Number).filter(Number.isFinite);
                const xValues = Array.isArray(xRaw) ? xRaw.map(Number).filter(Number.isFinite) : [];
                if (yValues.length > 0) {
                    return {
                        xValues: xValues.length === yValues.length ? xValues : null,
                        yValues,
                        xLabel: preview.x_axis || preview.xLabel || "Time (s)",
                        yLabel: preview.y_axis || preview.yLabel || "Amplitude",
                        tooltipLabel: preview.tooltip_label || "Amplitude",
                        title: preview.title || "Extracted Envelope Signal"
                    };
                }
            }
        }
    }

    if (Array.isArray(payload.envelope_time) && Array.isArray(payload.envelope_signal)) {
        const xValues = payload.envelope_time.map(Number).filter(Number.isFinite);
        const yValues = payload.envelope_signal.map(Number).filter(Number.isFinite);
        if (xValues.length === yValues.length && yValues.length > 0) {
            return {
                xValues,
                yValues,
                xLabel: "Time (s)",
                yLabel: "Amplitude",
                tooltipLabel: "Amplitude",
                title: "Extracted Envelope Signal"
            };
        }
    }

    const legacyCandidates = [
        payload.signal,
        payload.rssi_signal,
        payload.rssi_values,
        payload.rssi_preview,
        payload.preview_signal,
        payload.raw_rssi,
        payload.plot_data?.rssi,
        payload.chart?.rssi,
        data?.signal,
        data?.rssi_signal
    ];

    for (const candidate of legacyCandidates) {
        if (Array.isArray(candidate) && candidate.length > 0) {
            if (typeof candidate[0] === "number") {
                const yValues = candidate.map(Number).filter(Number.isFinite);
                if (yValues.length > 0) {
                    return {
                        xValues: null,
                        yValues,
                        xLabel: "Time (s)",
                        yLabel: "Amplitude",
                        tooltipLabel: "Amplitude",
                        title: "Envelope Signal Preview"
                    };
                }
            }
            if (typeof candidate[0] === "object") {
                const xValues = candidate.map(item => Number(item.time ?? item.t ?? item.x)).filter(Number.isFinite);
                const yValues = candidate.map(item => Number(item.value ?? item.amplitude ?? item.rssi ?? item.y)).filter(Number.isFinite);
                if (yValues.length > 0) {
                    return {
                        xValues: xValues.length === yValues.length ? xValues : null,
                        yValues,
                        xLabel: "Time (s)",
                        yLabel: "Amplitude",
                        tooltipLabel: "Amplitude",
                        title: "Envelope Signal Preview"
                    };
                }
            }
        }
    }
    return null;
}

function renderChart(signalData) {
    const canvas = document.getElementById("rssiChart");
    const placeholder = document.getElementById("signalPlaceholder");

    let yValues = [];
    let xValues = null;
    let xLabel = "Time (s)";
    let yLabel = "Amplitude";
    let tooltipLabel = "Amplitude";

    if (Array.isArray(signalData)) {
        yValues = signalData.map(Number).filter(Number.isFinite);
        xLabel = "Time (s)";
        xValues = yValues.map((_, index) => yValues.length > 1 ? (20 * index) / (yValues.length - 1) : 0);
    } else if (signalData && typeof signalData === "object") {
        yValues = Array.isArray(signalData.yValues) ? signalData.yValues.map(Number).filter(Number.isFinite) : [];
        if (Array.isArray(signalData.xValues)) {
            const cleanedX = signalData.xValues.map(Number).filter(Number.isFinite);
            if (cleanedX.length === yValues.length) xValues = cleanedX;
        }
        xLabel = signalData.xLabel || xLabel;
        yLabel = signalData.yLabel || yLabel;
        tooltipLabel = signalData.tooltipLabel || yLabel;
    }

    if (!yValues || yValues.length === 0) {
        canvas.style.display = "none";
        placeholder.style.display = "grid";
        placeholder.textContent = "Envelope preview available after selecting a test file";
        if (state.chart) {
            state.chart.destroy();
            state.chart = null;
        }
        return;
    }

    const cleanValues = yValues.filter((value) => Number.isFinite(value));
    if (cleanValues.length === 0) {
        canvas.style.display = "none";
        placeholder.style.display = "grid";
        placeholder.textContent = "Envelope preview available after selecting a test file";
        if (state.chart) {
            state.chart.destroy();
            state.chart = null;
        }
        return;
    }

    placeholder.style.display = "none";
    canvas.style.display = "block";

    const points = cleanValues.map((value, index) => ({
        x: xValues ? xValues[index] : (cleanValues.length > 1 ? (20 * index) / (cleanValues.length - 1) : 0),
        y: value
    }));

    const minValue = Math.min(...cleanValues);
    const maxValue = Math.max(...cleanValues);
    const padding = Math.max(0.08, (maxValue - minValue) * 0.12);
    const yMin = Math.min(-2, Math.floor((minValue - padding) * 2) / 2);
    const yMax = Math.max(1, Math.ceil((maxValue + padding) * 2) / 2);

    const xNumbers = points.map(p => p.x).filter(Number.isFinite);
    const xMinData = xNumbers.length ? Math.min(...xNumbers) : 1;
    const xMaxData = xNumbers.length ? Math.max(...xNumbers) : cleanValues.length;
    const usesTimeAxis = xLabel.toLowerCase().includes("time");
    const xMin = usesTimeAxis ? 0 : 1;
    const xMax = usesTimeAxis ? 20 : cleanValues.length;

    const ctx = canvas.getContext("2d");

    if (state.chart) {
        state.chart.destroy();
    }

    state.chart = new Chart(ctx, {
        type: "line",
        data: {
            datasets: [{
                label: yLabel,
                data: points,
                borderColor: "#2563eb",
                borderWidth: 1.8,
                tension: 0.12,
                pointRadius: 0,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            parsing: false,
            interaction: { intersect: false, mode: "nearest" },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (items) => {
                            if (!items.length) return "";
                            const x = Number(items[0].parsed.x);
                            return usesTimeAxis ? `Time: ${x.toFixed(2)} s` : `Sample ${Math.round(x)}`;
                        },
                        label: (context) => `${tooltipLabel}: ${Number(context.parsed.y).toFixed(3)}`
                    }
                }
            },
            scales: {
                x: {
                    type: "linear",
                    min: xMin,
                    max: xMax,
                    title: {
                        display: true,
                        text: xLabel,
                        color: "#475467",
                        font: { size: 12, weight: "600" }
                    },
                    grid: { color: "#eef2f7" },
                    ticks: {
                        color: "#667085",
                        maxTicksLimit: 11,
                        callback: (value) => usesTimeAxis ? Number(value).toFixed(0) : (Number.isInteger(value) ? value : "")
                    }
                },
                y: {
                    min: yMin,
                    max: yMax,
                    title: {
                        display: true,
                        text: yLabel,
                        color: "#475467",
                        font: { size: 12, weight: "600" }
                    },
                    grid: { color: "#eef2f7" },
                    ticks: {
                        color: "#667085",
                        maxTicksLimit: 7,
                        callback: (value) => `${value}`
                    }
                }
            }
        }
    });
}

async function loadHealth() {
    const card = document.getElementById("backendStatusCard");
    const status = document.getElementById("backendStatus");
    const icon = document.getElementById("backendIcon");

    try {
        await safeFetch(`${API_BASE_URL}/health`);
        card.classList.remove("status-disconnected");
        card.classList.add("status-connected");
        status.textContent = "Backend Connected";
        if (icon) icon.textContent = "✓";
    } catch {
        card.classList.remove("status-connected");
        card.classList.add("status-disconnected");
        status.textContent = "Backend Disconnected";
        if (icon) icon.textContent = "!";
    }
}

async function loadModelInfo() {
    try {
        state.modelInfo = await safeFetch(`${API_BASE_URL}/model-info`);
    } catch {
        state.modelInfo = {};
    }
    renderModelInfo();
}

async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/history?limit=50`);
        if (!response.ok) throw new Error("History failed");
        const data = await response.json();
        const records = Array.isArray(data) ? data : data.items || data.records || data.history || [];
        state.history = Array.isArray(records) ? records : [];
        renderHistory();
        updateLastClassificationTime();
        setMessage("historyMessage", "");
    } catch {
        state.history = [];
        renderHistory();
        updateLastClassificationTime();
        setMessage("historyMessage", "Unable to load detection history at the moment.", "error");
    }
}

function updateLastClassificationTime() {
    const latest = getLatestHistoryRecord(state.history);
    document.getElementById("lastClassification").textContent = latest
        ? `Last: ${formatMalaysiaTimestamp(getRecordTimestamp(latest))}`
        : "Last: No record yet";
}

function getRecordActivity(record) {
    return normalizeActivity(record.prediction_text || record.classified_activity || record.activity || record.classification || record.result);
}

function cleanDisplayFileName(value) {
    if (value === undefined || value === null || value === "") return "—";
    const text = String(value).replaceAll("\\", "/");
    const parts = text.split("/");
    return parts[parts.length - 1] || text;
}

function getRecordFileName(record) {
    return cleanDisplayFileName(record.file_name || record.filename || record.uploaded_file_name || "—");
}

function getRecordConfidence(record) {
    const activity = getRecordActivity(record);
    const pair = getConfidencePair(record, activity);
    return formatPercent(pair.fallConfidence);
}

function getInputMode(record) {
    const mode = record.input_mode || "OFFICIAL TEST UPLOAD LOOKUP";
    const upper = String(mode).replace(/_/g, " ").toUpperCase();
    if (upper.includes("UPLOAD")) return "OFFICIAL TEST UPLOAD";
    if (upper.includes("OFFICIAL")) return "OFFICIAL TEST LOOKUP";
    if (upper.includes("LIVE")) return "LIVE MONITORING";
    return "OFFICIAL TEST LOOKUP";
}

function getStatus(record, activity) {
    return record.status || (activity === "Fall" ? "Alert" : "Normal");
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function renderHistory() {
    const body = document.getElementById("historyBody");
    const records = state.history;

    if (!Array.isArray(records) || records.length === 0) {
        body.innerHTML = `<tr><td colspan="9">No detection history available</td></tr>`;
        return;
    }

    body.innerHTML = records.map(record => {
        const id = record.id;
        const activity = getRecordActivity(record);
        const fall = activity === "Fall";
        const risk = record.risk_level || (fall ? "High" : "Low");
        const mode = getInputMode(record);
        const status = getStatus(record, activity);
        const statusClass = String(status).toLowerCase().includes("alert") ? "badge-alert" : "badge-normal";
        const activityClass = fall ? "badge-fall" : "badge-normal";
        const riskClass = String(risk).toLowerCase().includes("high") ? "badge-high" : "badge-low";

        return `
            <tr>
                <td>${formatMalaysiaTimestamp(getRecordTimestamp(record))}</td>
                <td>${escapeHtml(getRecordFileName(record))}</td>
                <td><span class="badge ${activityClass}">${escapeHtml(activity || "—")}</span></td>
                <td>${getRecordConfidence(record)}</td>
                <td><span class="badge ${riskClass}">${escapeHtml(risk || "—")}</span></td>
                <td><span class="badge badge-manual">${escapeHtml(mode)}</span></td>
                <td>${formatSeconds(record.processing_time_sec ?? record.processing_time)}</td>
                <td><span class="badge ${statusClass}">${escapeHtml(status)}</span></td>
                <td>
                    <button class="delete-record-btn" title="Delete record" aria-label="Delete record" onclick="deleteRecord('${escapeHtml(id)}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M3 6h18"></path>
                            <path d="M8 6V4h8v2"></path>
                            <path d="M19 6l-1 14H6L5 6"></path>
                            <path d="M10 11v6"></path>
                            <path d="M14 11v6"></path>
                        </svg>
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}


async function loadSampleFiles() {
    const select = document.getElementById("sampleDataSelect");
    if (!select) return;

    try {
        const response = await fetch(`${API_BASE_URL}/testing/sample-files`);
        if (!response.ok) throw new Error("Sample file list failed");

        const data = await response.json();
        const items = Array.isArray(data.items) ? data.items : [];

        state.sampleFiles = items;
        renderSampleFileOptions();
        setMessage("sampleMessage", "");

    } catch {
        state.sampleFiles = [];
        renderSampleFileOptions();
        setMessage("sampleMessage", "Saved testing data is unavailable until Render is redeployed.", "error");
    }
}


function renderSampleFileOptions() {
    const select = document.getElementById("sampleDataSelect");
    if (!select) return;

    if (!Array.isArray(state.sampleFiles) || state.sampleFiles.length === 0) {
        select.innerHTML = `<option value="">No saved testing data available</option>`;
        state.selectedSamplePath = "";
        return;
    }

    select.innerHTML = `<option value="">Choose saved testing data...</option>` + state.sampleFiles.map(item => {
        const label = item.display_label || `${item.event || ""} / ${item.file_name || ""}`.replace(/^ \/ /, "");
        return `<option value="${escapeHtml(item.relative_path)}">${escapeHtml(label)}</option>`;
    }).join("");
}


function handleSampleSelect() {
    const select = document.getElementById("sampleDataSelect");
    state.selectedSamplePath = select ? select.value : "";
    setMessage("sampleMessage", "");
}


async function loadSelectedSample() {
    setMessage("sampleMessage", "");

    const select = document.getElementById("sampleDataSelect");
    const relativePath = select ? select.value : "";

    if (!relativePath) {
        setMessage("sampleMessage", "Please choose one saved testing file first.", "error");
        return;
    }

    const selectedItem = state.sampleFiles.find(item => item.relative_path === relativePath) || {};
    const displayName = selectedItem.file_name || relativePath.split("/").pop() || "saved testing file";

    clearClassification(displayName);
    setLoading("sampleBtn", true, "Loading saved data...");

    try {
        const data = await safeFetch(`${API_BASE_URL}/predict/sample`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ relative_path: relativePath })
        });

        const result = extractPredictionData(data);
        if (!result) throw new Error("Unsupported");

        state.currentFile = displayName;
        state.currentResult = result;
        renderResult();

        const signal = extractSignal(data);
        renderChart(signal);

        await loadHistory();
        setMessage("uploadMessage", "");

    } catch {
        clearClassification(displayName);
        renderChart(null);
        setMessage("sampleMessage", friendlyErrorMessage(), "error");

    } finally {
        setLoading("sampleBtn", false);
    }
}


function handleFileSelect() {
    const input = document.getElementById("fileUpload");

    state.selectedFile = input.files && input.files.length > 0 ? input.files[0] : null;

    document.getElementById("selectedFileName").textContent =
        state.selectedFile ? state.selectedFile.name : "No file selected";

    setMessage("uploadMessage", "");

    if (state.selectedFile) {
        const fileName = state.selectedFile.name || "";

        if (!fileName.toLowerCase().endsWith(".mat")) {
            clearClassification(fileName);
            renderChart(null);
            setMessage("uploadMessage", "Please upload a .mat file.", "error");
            return;
        }

        uploadAndClassify();
    }
}


async function uploadAndClassify() {
    setMessage("uploadMessage", "");

    if (!state.selectedFile) {
        clearClassification(null);
        setMessage("uploadMessage", "Please upload a .mat file first.", "error");
        return;
    }

    clearClassification(state.selectedFile.name);
    setMessage("uploadMessage", "Checking uploaded .mat file...", "info");

    const formData = new FormData();
    formData.append("file", state.selectedFile);

    try {
        const response = await fetch(`${API_BASE_URL}/predict/batch`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) throw new Error("Upload failed");

        const data = await response.json();

        const result = extractPredictionData(data);
        if (!result) throw new Error("Unsupported");

        state.currentFile = state.selectedFile.name;
        state.currentResult = result;
        renderResult();

        const signal = extractSignal(data);
        renderChart(signal);

        await loadHistory();
        setMessage("uploadMessage", "");

    } catch {
        clearClassification(state.selectedFile ? state.selectedFile.name : null);
        renderChart(null);
        setMessage("uploadMessage", friendlyErrorMessage(), "error");
    }
}


async function deleteRecord(recordId) {
    if (!recordId || recordId === "undefined" || recordId === "null") {
        setMessage("historyMessage", "This history row cannot be deleted because it has no record ID.", "error");
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/history/${recordId}`, {
            method: "DELETE"
        });
        if (!response.ok) throw new Error("Delete failed");
        await loadHistory();
    } catch {
        setMessage("historyMessage", "Unable to delete this record. Please try again.", "error");
    }
}

async function clearAllHistory() {
    const confirmed = window.confirm("Clear all official test check history?");
    if (!confirmed) return;

    const btn = document.getElementById("clearAllBtn");
    btn.disabled = true;
    try {
        const response = await fetch(`${API_BASE_URL}/history/all?confirm=true`, {
            method: "DELETE"
        });
        if (!response.ok) throw new Error("Clear all failed");
        await loadHistory();
    } catch {
        setMessage("historyMessage", "Unable to clear all history. Please try again.", "error");
    } finally {
        btn.disabled = false;
    }
}

async function bootDashboard() {
    renderResult();
    renderChart(null);
    await Promise.all([
        loadHealth(),
        loadModelInfo(),
        loadHistory(),
        loadSampleFiles()
    ]);
}

document.addEventListener("DOMContentLoaded", bootDashboard);

function resizeStreamlitFrameToDashboard() {
    const dashboard = document.querySelector(".dashboard");
    if (!dashboard) return;
    const rect = dashboard.getBoundingClientRect();
    const height = Math.ceil(rect.height + 48);
    window.parent.postMessage({
        isStreamlitMessage: true,
        type: "streamlit:setFrameHeight",
        height: height
    }, "*");
}

window.addEventListener("load", resizeStreamlitFrameToDashboard);
window.addEventListener("resize", resizeStreamlitFrameToDashboard);
setTimeout(resizeStreamlitFrameToDashboard, 150);
setTimeout(resizeStreamlitFrameToDashboard, 700);
try {
    const dashboardObserver = new ResizeObserver(resizeStreamlitFrameToDashboard);
    dashboardObserver.observe(document.querySelector(".dashboard"));
} catch (error) {
    // ResizeObserver is optional; fixed height still works if unavailable.
}


/* FINAL RESPONSIVE HEIGHT RESIZER */
function resizeStreamlitFrameToDashboard() {
    const dashboard = document.querySelector(".dashboard");
    if (!dashboard) return;

    const body = document.body;
    const html = document.documentElement;
    const dashboardHeight = dashboard.scrollHeight || dashboard.getBoundingClientRect().height || 0;
    const bodyHeight = body ? body.scrollHeight : 0;
    const htmlHeight = html ? html.scrollHeight : 0;
    const height = Math.ceil(Math.max(dashboardHeight, bodyHeight, htmlHeight) + 10);

    window.parent.postMessage({
        isStreamlitMessage: true,
        type: "streamlit:setFrameHeight",
        height: height
    }, "*");
}

function queueDashboardResize() {
    window.requestAnimationFrame(() => {
        resizeStreamlitFrameToDashboard();
        setTimeout(resizeStreamlitFrameToDashboard, 80);
    });
}

window.addEventListener("load", queueDashboardResize);
window.addEventListener("resize", queueDashboardResize);
window.addEventListener("orientationchange", queueDashboardResize);
setTimeout(queueDashboardResize, 150);
setTimeout(queueDashboardResize, 700);
setTimeout(queueDashboardResize, 1400);

try {
    const responsiveDashboardObserver = new MutationObserver(queueDashboardResize);
    responsiveDashboardObserver.observe(document.querySelector(".dashboard"), {
        childList: true,
        subtree: true,
        attributes: true
    });
} catch (error) {
    // Fixed iframe fallback remains available if MutationObserver is unavailable.
}

</script>
</body>
</html>
"""

components.html(DASHBOARD_HTML, height=900, scrolling=True)
