import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Wi-Fi Fall Detection Dashboard", page_icon="📡", layout="wide")

DEFAULT_TRAINVAL_DIR = Path("trainval")

DISPLAY_NAME = {
    "FFT": "FFT",
    "STFT": "STFT",
    "CWT": "CWT",
    "Balanced_COMB": "Balanced COMB"
}

REQUIRED_FILES = {
    "OOF predictions": "oof_predictions_by_file.csv",
    "OOF summary": "oof_summary_four_sets.csv",
    "Final ranking": "final_model_ranking_cv_selected_threshold.csv",
    "CV summary": "cv_summary_four_sets.csv",
    "Fold details": "all_folds_four_sets.csv",
    "OOF errors": "oof_errors_only.csv"
}

OPTIONAL_FILES = {
    "CV aggregated summary": "cv_aggregated_selected_threshold_summary.csv",
    "Fold winners": "fold_winners_four_sets.csv",
    "Split manifest": "split_manifest_outer.csv",
    "COMB selected features": "comb_selected_features_cv.csv"
}

PLOT_FOLDERS = {
    "Confusion Matrices": Path("plots") / "01_confusion_matrices",
    "ROC Curves": Path("plots") / "02_roc_curves",
    "PR Curves": Path("plots") / "03_pr_curves",
    "Fit Curves": Path("plots") / "04_fit_curves",
    "Feature Importance": Path("plots") / "05_feature_importance",
    "Threshold Sensitivity": Path("plots") / "06_threshold_sensitivity",
    "Comparison": Path("plots") / "07_comparison"
}

METRIC_COLUMNS = {
    "Accuracy": "OOF_Accuracy_SelectedThr",
    "F1 Score": "OOF_F1_SelectedThr",
    "Balanced Accuracy": "OOF_BalAcc_SelectedThr",
    "Precision": "OOF_Precision_SelectedThr",
    "Recall": "OOF_Recall_SelectedThr",
    "Specificity": "OOF_Specificity_SelectedThr",
    "ROC AUC": "OOF_ROC_AUC",
    "PR AUC": "OOF_PR_AUC"
}

RANKING_COLUMNS = {
    "CV Accuracy": "CV_SelectedThr_Accuracy",
    "CV F1 Score": "CV_SelectedThr_F1",
    "CV Balanced Accuracy": "CV_SelectedThr_BalancedAccuracy",
    "CV Precision": "CV_SelectedThr_Precision",
    "CV Recall": "CV_SelectedThr_Recall",
    "CV Specificity": "CV_SelectedThr_Specificity"
}

FOLD_METRIC_COLUMNS = {
    "Fold Accuracy": "FoldVal_Accuracy_SelectedThr",
    "Fold F1 Score": "FoldVal_F1_SelectedThr",
    "Fold Balanced Accuracy": "FoldVal_BalancedAccuracy_SelectedThr",
    "Fold Precision": "FoldVal_Precision_SelectedThr",
    "Fold Recall": "FoldVal_Recall_SelectedThr",
    "Fold Specificity": "FoldVal_Specificity_SelectedThr"
}


def path_from_text(folder_text: str) -> Path:
    cleaned = folder_text.strip().strip('"').strip("'")
    return Path(cleaned)


def file_path(base_dir: Path, filename: str) -> Path:
    return base_dir / filename


@st.cache_data(show_spinner=False)
def read_csv_cached(path_text: str) -> pd.DataFrame:
    return pd.read_csv(path_text)


def load_csv_if_exists(base_dir: Path, filename: str) -> pd.DataFrame | None:
    path = file_path(base_dir, filename)
    if path.exists():
        return read_csv_cached(str(path))
    return None


def dataset_label(dataset_name: str) -> str:
    return DISPLAY_NAME.get(dataset_name, dataset_name)


def format_pct(value) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{float(value) * 100:.2f}%"


def add_label_names(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "Label" in out.columns:
        out["Actual"] = out["Label"].map({0: "Non-Fall", 1: "Fall"}).fillna(out["Label"].astype(str))
    if "PredLabel" in out.columns:
        out["Prediction"] = out["PredLabel"].map({0: "Non-Fall", 1: "Fall"}).fillna(out["PredLabel"].astype(str))
    if "Correct" in out.columns:
        out["Result"] = out["Correct"].map({1: "Correct", 0: "Wrong"}).fillna(out["Correct"].astype(str))
    if "PredProb" in out.columns:
        out["Fall Probability (%)"] = (out["PredProb"].astype(float) * 100).round(2)
    return out


def show_missing_file_warning(base_dir: Path) -> bool:
    missing = []
    for label, filename in REQUIRED_FILES.items():
        if not file_path(base_dir, filename).exists():
            missing.append(f"{label}: {filename}")
    if missing:
        st.error("Some required dashboard files are missing from the selected trainval folder.")
        st.write("Missing files:")
        for item in missing:
            st.write(f"- {item}")
        st.info("Run LGBM_8_TrainOnly.py first, then select the generated trainval folder.")
        return False
    return True


def build_confusion_matrix(df: pd.DataFrame) -> pd.DataFrame:
    cm = pd.crosstab(df["Label"], df["PredLabel"], rownames=["Actual"], colnames=["Predicted"], dropna=False)
    cm = cm.reindex(index=[0, 1], columns=[0, 1], fill_value=0)
    cm.index = ["Non-Fall", "Fall"]
    cm.columns = ["Non-Fall", "Fall"]
    return cm


def plot_confusion_matrix(cm: pd.DataFrame, title: str):
    fig = px.imshow(
        cm,
        text_auto=True,
        aspect="auto",
        labels=dict(x="Predicted Label", y="Actual Label", color="Count"),
        title=title
    )
    fig.update_layout(height=430)
    st.plotly_chart(fig, use_container_width=True)


def metric_card(label: str, value):
    st.metric(label=label, value=format_pct(value))


def show_header():
    st.title("Wi-Fi-Based Fall Detection Dashboard")
    st.caption("Training-validation result visualization using OOF/CV output files from the LightGBM pipeline.")


def show_file_status(base_dir: Path):
    with st.expander("Dashboard file status", expanded=False):
        rows = []
        for label, filename in {**REQUIRED_FILES, **OPTIONAL_FILES}.items():
            path = file_path(base_dir, filename)
            rows.append({"File Purpose": label, "Filename": filename, "Found": "Yes" if path.exists() else "No"})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def show_overview(oof_summary: pd.DataFrame, final_rank: pd.DataFrame, oof_predictions: pd.DataFrame):
    st.subheader("Overall Dashboard Summary")
    best_dataset = str(final_rank.sort_values("Rank").iloc[0]["Dataset"])
    best_display = dataset_label(best_dataset)
    best_oof = oof_summary[oof_summary["Dataset"] == best_dataset]
    if len(best_oof) == 0:
        best_oof = oof_summary.iloc[[0]]
    best_row = best_oof.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Best Ranked Feature Set", best_display)
    with c2:
        metric_card("OOF Accuracy", best_row.get("OOF_Accuracy_SelectedThr"))
    with c3:
        metric_card("OOF F1 Score", best_row.get("OOF_F1_SelectedThr"))
    with c4:
        metric_card("OOF Specificity", best_row.get("OOF_Specificity_SelectedThr"))
    st.write("This dashboard shows the training-validation achievement from the saved OOF/CV results. It does not retrain the model inside the interface.")
    count_df = oof_predictions.groupby("Dataset").size().reset_index(name="Number of OOF Predictions")
    count_df["Feature Set"] = count_df["Dataset"].map(dataset_label)
    fig = px.bar(count_df, x="Feature Set", y="Number of OOF Predictions", text="Number of OOF Predictions", title="Number of OOF Predictions by Feature Set")
    fig.update_traces(textposition="outside")
    fig.update_layout(height=430, yaxis_title="Number of Predictions")
    st.plotly_chart(fig, use_container_width=True)


def show_model_comparison(oof_summary: pd.DataFrame, final_rank: pd.DataFrame, cv_summary: pd.DataFrame):
    st.subheader("Model Performance Comparison")
    display_oof = oof_summary.copy()
    display_oof["Feature Set"] = display_oof["Dataset"].map(dataset_label)
    available_metrics = [label for label, col in METRIC_COLUMNS.items() if col in display_oof.columns]
    selected_metrics = st.multiselect("Select metrics to compare", available_metrics, default=[m for m in ["Accuracy", "F1 Score", "Balanced Accuracy", "Specificity"] if m in available_metrics])
    if selected_metrics:
        plot_df = display_oof[["Feature Set"] + [METRIC_COLUMNS[m] for m in selected_metrics]].melt(id_vars="Feature Set", var_name="Metric", value_name="Score")
        reverse_map = {v: k for k, v in METRIC_COLUMNS.items()}
        plot_df["Metric"] = plot_df["Metric"].map(reverse_map)
        fig = px.bar(plot_df, x="Feature Set", y="Score", color="Metric", barmode="group", text=plot_df["Score"].apply(lambda x: f"{x * 100:.1f}%"), title="OOF Performance Comparison")
        fig.update_yaxes(range=[0, 1])
        fig.update_layout(height=500, yaxis_tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)
    st.write("Final model ranking based on CV selected-threshold result:")
    rank_show = final_rank.copy()
    rank_show["Feature Set"] = rank_show["Dataset"].map(dataset_label)
    for col in RANKING_COLUMNS.values():
        if col in rank_show.columns:
            rank_show[col] = rank_show[col].apply(format_pct)
    desired_cols = ["Rank", "Feature Set"] + [col for col in RANKING_COLUMNS.values() if col in rank_show.columns] + ["CV_SelectedThr_TotalErrors"]
    st.dataframe(rank_show[desired_cols], use_container_width=True, hide_index=True)
    with st.expander("CV summary table", expanded=False):
        st.dataframe(cv_summary, use_container_width=True, hide_index=True)


def show_prediction_explorer(oof_predictions: pd.DataFrame, selected_dataset: str):
    st.subheader("OOF Prediction Explorer")
    df = oof_predictions[oof_predictions["Dataset"] == selected_dataset].copy()
    df = add_label_names(df)
    c1, c2, c3 = st.columns(3)
    with c1:
        event_options = sorted(df["Event"].dropna().unique().tolist()) if "Event" in df.columns else []
        selected_events = st.multiselect("Filter by event", event_options, default=event_options)
    with c2:
        result_options = ["Correct", "Wrong"]
        selected_results = st.multiselect("Filter by result", result_options, default=result_options)
    with c3:
        prob_range = st.slider("Fall probability range (%)", 0, 100, (0, 100))
    if selected_events and "Event" in df.columns:
        df = df[df["Event"].isin(selected_events)]
    if selected_results and "Result" in df.columns:
        df = df[df["Result"].isin(selected_results)]
    if "Fall Probability (%)" in df.columns:
        df = df[(df["Fall Probability (%)"] >= prob_range[0]) & (df["Fall Probability (%)"] <= prob_range[1])]
    st.write(f"Showing {len(df)} prediction rows for {dataset_label(selected_dataset)}.")
    table_cols = [col for col in ["File", "Event", "Actual", "Prediction", "Fall Probability (%)", "Result"] if col in df.columns]
    st.dataframe(df[table_cols], use_container_width=True, hide_index=True)
    if len(df) > 0 and "PredProb" in df.columns:
        fig = px.histogram(df, x="Fall Probability (%)", color="Result", nbins=20, title="Prediction Probability Distribution")
        fig.update_layout(height=430)
        st.plotly_chart(fig, use_container_width=True)


def show_error_analysis(oof_predictions: pd.DataFrame, oof_errors: pd.DataFrame, selected_dataset: str):
    st.subheader("Error Analysis")
    df = oof_predictions[oof_predictions["Dataset"] == selected_dataset].copy()
    if len(df) == 0:
        st.warning("No prediction data found for this feature set.")
        return
    cm = build_confusion_matrix(df)
    plot_confusion_matrix(cm, f"OOF Confusion Matrix - {dataset_label(selected_dataset)}")
    err = df[df["Correct"] == 0].copy()
    if len(err) == 0:
        st.success("No OOF errors for the selected feature set.")
        return
    err_by_event = err.groupby("Event").size().reset_index(name="Number of Errors").sort_values("Number of Errors", ascending=False)
    fig = px.bar(err_by_event, x="Event", y="Number of Errors", text="Number of Errors", title="OOF Errors by Event")
    fig.update_traces(textposition="outside")
    fig.update_layout(height=450, xaxis_tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)
    err = add_label_names(err)
    table_cols = [col for col in ["File", "Event", "Actual", "Prediction", "Fall Probability (%)", "Result"] if col in err.columns]
    st.write("Wrong prediction rows:")
    st.dataframe(err[table_cols], use_container_width=True, hide_index=True)
    if oof_errors is not None and len(oof_errors) > 0:
        with st.expander("Original oof_errors_only.csv", expanded=False):
            st.dataframe(oof_errors[oof_errors["Dataset"] == selected_dataset], use_container_width=True, hide_index=True)


def show_fold_analysis(folds: pd.DataFrame, selected_dataset: str):
    st.subheader("Fold-by-Fold Analysis")
    df = folds[folds["Dataset"] == selected_dataset].copy()
    if len(df) == 0:
        st.warning("No fold data found for this feature set.")
        return
    available_metrics = [label for label, col in FOLD_METRIC_COLUMNS.items() if col in df.columns]
    metric_choice = st.selectbox("Select fold metric", available_metrics, index=0)
    metric_col = FOLD_METRIC_COLUMNS[metric_choice]
    fig = px.line(df, x="Fold", y=metric_col, markers=True, title=f"{metric_choice} across 5 folds - {dataset_label(selected_dataset)}")
    fig.update_yaxes(range=[0, 1], tickformat=".0%")
    fig.update_layout(height=430)
    st.plotly_chart(fig, use_container_width=True)
    show_cols = ["Fold", "NumFeaturesUsed", "BestIteration", "SelectedThreshold", "ConstraintMet", "FitDiagnosis"]
    show_cols += [col for col in FOLD_METRIC_COLUMNS.values() if col in df.columns]
    st.dataframe(df[[col for col in show_cols if col in df.columns]], use_container_width=True, hide_index=True)


def show_saved_plots(base_dir: Path):
    st.subheader("Saved Plot Viewer")
    folder_label = st.selectbox("Select plot folder", list(PLOT_FOLDERS.keys()))
    plot_dir = base_dir / PLOT_FOLDERS[folder_label]
    if not plot_dir.exists():
        st.warning(f"Plot folder not found: {plot_dir}")
        return
    image_files = sorted([p for p in plot_dir.glob("*.png")])
    if not image_files:
        st.warning("No PNG images found in this folder.")
        return
    image_names = [p.name for p in image_files]
    selected_image_name = st.selectbox("Select image", image_names)
    selected_image = plot_dir / selected_image_name
    st.image(str(selected_image), caption=selected_image_name, use_container_width=True)


def show_comb_features(comb_features: pd.DataFrame | None):
    st.subheader("Balanced COMB Selected Features")
    if comb_features is None or len(comb_features) == 0:
        st.warning("comb_selected_features_cv.csv was not found or is empty.")
        return
    if "FeatureBlock" in comb_features.columns:
        block_count = comb_features.groupby("FeatureBlock").size().reset_index(name="Selected Count")
        fig = px.bar(block_count, x="FeatureBlock", y="Selected Count", text="Selected Count", title="Selected COMB Features by Block")
        fig.update_traces(textposition="outside")
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(comb_features, use_container_width=True, hide_index=True)


def main():
    show_header()
    st.sidebar.header("Dashboard Settings")
    folder_text = st.sidebar.text_input("Trainval result folder", value=DEFAULT_TRAINVAL_DIR)
    base_dir = path_from_text(folder_text)
    st.sidebar.caption("Use the folder that contains oof_predictions_by_file.csv and oof_summary_four_sets.csv.")
    st.write(f"Selected folder: `{base_dir}`")
    show_file_status(base_dir)
    if not base_dir.exists():
        st.error("The selected folder does not exist. Please check the folder path.")
        return
    if not show_missing_file_warning(base_dir):
        return
    oof_predictions = load_csv_if_exists(base_dir, REQUIRED_FILES["OOF predictions"])
    oof_summary = load_csv_if_exists(base_dir, REQUIRED_FILES["OOF summary"])
    final_rank = load_csv_if_exists(base_dir, REQUIRED_FILES["Final ranking"])
    cv_summary = load_csv_if_exists(base_dir, REQUIRED_FILES["CV summary"])
    folds = load_csv_if_exists(base_dir, REQUIRED_FILES["Fold details"])
    oof_errors = load_csv_if_exists(base_dir, REQUIRED_FILES["OOF errors"])
    comb_features = load_csv_if_exists(base_dir, OPTIONAL_FILES["COMB selected features"])
    datasets = sorted(oof_predictions["Dataset"].dropna().unique().tolist())
    default_dataset = "Balanced_COMB" if "Balanced_COMB" in datasets else datasets[0]
    selected_dataset = st.sidebar.selectbox("Feature set", datasets, index=datasets.index(default_dataset), format_func=dataset_label)
    tab_overview, tab_compare, tab_predictions, tab_errors, tab_folds, tab_plots, tab_comb = st.tabs([
        "Overview",
        "Model Comparison",
        "Prediction Explorer",
        "Error Analysis",
        "Fold Analysis",
        "Saved Plots",
        "COMB Features"
    ])
    with tab_overview:
        show_overview(oof_summary, final_rank, oof_predictions)
    with tab_compare:
        show_model_comparison(oof_summary, final_rank, cv_summary)
    with tab_predictions:
        show_prediction_explorer(oof_predictions, selected_dataset)
    with tab_errors:
        show_error_analysis(oof_predictions, oof_errors, selected_dataset)
    with tab_folds:
        show_fold_analysis(folds, selected_dataset)
    with tab_plots:
        show_saved_plots(base_dir)
    with tab_comb:
        show_comb_features(comb_features)


if __name__ == "__main__":
    main()
