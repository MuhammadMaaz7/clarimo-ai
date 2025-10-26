#!/usr/bin/env python3
"""
thematic_clustering.py
----------------------
Clusters semantically filtered posts into problem themes / pain points.

Input:  filtered_posts.json (from semantic_filter.py)
Output: cluster_summary.json, cluster_posts.json, cluster_visualization.png (optional)
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import hdbscan
import umap
import matplotlib.pyplot as plt
from sentence_transformers import SentenceTransformer
import os
import sys
from datetime import datetime
import argparse
from sklearn.preprocessing import normalize

# ------------------------
# Config
# ------------------------
MODEL_NAME = "mixedbread-ai/mxbai-embed-large-v1"
MIN_CLUSTER_SIZE = 10
UMAP_N_COMPONENTS = 20
UMAP_N_NEIGHBORS = 15
OUTPUT_DIR = "clusters_out3"

# ------------------------
# Load Data
# ------------------------
def load_filtered_posts(filtered_path: Path):
    with open(filtered_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    texts = [d.get("text") or d.get("content") or "" for d in data]
    return data, texts

# ------------------------
# Embedding
# ------------------------
def get_embeddings(texts, model_name=MODEL_NAME):
    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    return embeddings

# ------------------------
# Dimensionality Reduction (UMAP)
# ------------------------
def reduce_embeddings(embeddings):
    print("Reducing dimensions with UMAP for clustering...")
    reducer = umap.UMAP(
        n_neighbors=UMAP_N_NEIGHBORS,
        n_components=UMAP_N_COMPONENTS,
        metric='cosine',
        random_state=42
    )
    return reducer.fit_transform(embeddings)

# ------------------------
# Clustering (HDBSCAN)
# ------------------------
def cluster_embeddings(embeddings):
    print("Clustering embeddings with HDBSCAN...")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=2,
        metric='euclidean',
        cluster_selection_method='eom'
    )
    cluster_labels = clusterer.fit_predict(embeddings)
    print(f"✅ Found {len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)} clusters.")
    return cluster_labels

# ------------------------
# Summarize Clusters
# ------------------------
def summarize_clusters(texts, cluster_labels, outdir):
    df = pd.DataFrame({"text": texts, "cluster": cluster_labels})
    clusters = {}
    for label, group in df.groupby("cluster"):
        if label == -1:
            continue  # ignore noise
        sample_texts = group["text"].head(15).tolist()
        clusters[int(label)] = {
            "count": len(group),
            "sample_posts": sample_texts
        }

    summary_path = Path(outdir) / "cluster_summary.json"
    posts_path = Path(outdir) / "cluster_posts.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(clusters, f, indent=2)
    df.to_json(posts_path, orient="records", indent=2)
    print(f"🧩 Cluster summaries saved to {summary_path}")
    return clusters, df

# ------------------------
# Optional Visualization
# ------------------------
def plot_clusters(embeddings_2d, cluster_labels, outdir):
    print("Plotting clusters...")
    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(
        embeddings_2d[:, 0], embeddings_2d[:, 1],
        c=cluster_labels, cmap="tab10", s=10, alpha=0.7
    )
    plt.colorbar(scatter)
    plt.title("Thematic Clusters (UMAP 2D)")
    plt.tight_layout()
    plt.savefig(Path(outdir) / "cluster_visualization.png")
    plt.close()
    print("🖼️ Cluster visualization saved.")

# ------------------------
# Main
# ------------------------
def main():
    parser = argparse.ArgumentParser(description="Cluster semantically filtered posts into problem themes.")
    parser.add_argument("--input", required=True, help="Path to filtered_posts.json")
    parser.add_argument("--outdir", default="clusters_out", help="Directory to save clustering outputs")
    args = parser.parse_args()

    input_path = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(exist_ok=True, parents=True)

    print(f"📥 Loading filtered posts from: {input_path}")
    print(f"📂 Output directory: {outdir}")

    data, texts = load_filtered_posts(input_path)
    embeddings = get_embeddings(texts)
    reduced = reduce_embeddings(embeddings)
    reduced = normalize(reduced, norm='l2')
    

    cluster_labels = cluster_embeddings(reduced)
    summarize_clusters(texts, cluster_labels, outdir)
    #new
    unique_labels, counts = np.unique(cluster_labels, return_counts=True)
    print("Cluster distribution:", dict(zip(unique_labels, counts)))

    # Optional: 2D visualization
    pca_2d = PCA(n_components=2).fit_transform(reduced)
    plot_clusters(pca_2d, cluster_labels, outdir)


if __name__ == "__main__":
    main()