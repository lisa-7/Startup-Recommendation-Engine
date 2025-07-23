import pandas as pd
from fuzzywuzzy import fuzz
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

def match_score(founder, provider):
    score = 0
    reason = []

    # 1. Industry match (25 points)
    if founder['startup_industry'] == provider['industry_preference']:
        score += 25
        reason.append("Industry aligned")
    else:
        score += 10
        reason.append("Different industry")

    # 2. Skill match (25 points)
    tech_ratio = fuzz.partial_ratio(str(founder['tech_requirement']), str(provider['core_skill']))
    skill_score = (tech_ratio / 100) * 25
    score += skill_score
    reason.append(f"Skill match: {tech_ratio}%")

    # 3. Project type match (20 points)
    if founder['project_need'] == provider['preferred_project_type']:
        score += 20
        reason.append("Project type fits")
    else:
        score += 8
        reason.append("Partial project type fit")

    # 4. Timeline match (20 points)
    time_ratio = fuzz.partial_ratio(str(founder['project_deadline']), str(provider['availability']))
    time_score = (time_ratio / 100) * 20
    score += time_score
    reason.append(f"Timeline fit: {time_ratio}%")

    # 5. Startup stage ↔ expertise area (10 points)
    stage_ratio = fuzz.partial_ratio(str(founder['startup_stage']), str(provider['expertise_area']))
    stage_score = (stage_ratio / 100) * 10
    score += stage_score
    reason.append(f"Stage match: {stage_ratio}%")

    return round(score, 2), "; ".join(reason)


def generate_matches(df):
    founders = df[df["user_id"].str.startswith("F")].copy()
    providers = df[df["user_id"].str.startswith("S")].copy()

    founder_matches = []
    provider_matches = []

    for _, f in founders.iterrows():
        scores = []
        for _, p in providers.iterrows():
            s, r = match_score(f, p)
            scores.append((f['user_id'], p['user_id'], s, r))
        top = sorted(scores, key=lambda x: x[2], reverse=True)[:5]
        founder_matches.extend(top)

    for _, p in providers.iterrows():
        scores = []
        for _, f in founders.iterrows():
            s, r = match_score(f, p)
            scores.append((p['user_id'], f['user_id'], s, r))
        top = sorted(scores, key=lambda x: x[2], reverse=True)[:5]
        provider_matches.extend(top)

    founder_df = pd.DataFrame(founder_matches, columns=["founder_id", "provider_id", "match_score", "reason"])
    provider_df = pd.DataFrame(provider_matches, columns=["provider_id", "founder_id", "match_score", "reason"])
    return founder_df, provider_df


import matplotlib.pyplot as plt
import seaborn as sns

def generate_match_heatmap(founders, providers, get_user_name, filename="match_matrix_heatmap.png"):
    """
    Generates and saves a heatmap of match scores between founders and providers.

    Parameters:
        founders (DataFrame): DataFrame containing founder profiles
        providers (DataFrame): DataFrame containing provider profiles
        get_user_name (function): Function that maps user_id to a display name
        filename (str): Output file name for the heatmap image
    """

    # Create match score matrix
    matrix = np.zeros((len(founders), len(providers)))
    for i, (_, founder) in enumerate(founders.iterrows()):
        for j, (_, provider) in enumerate(providers.iterrows()):
            score, _ = match_score(founder, provider)
            matrix[i][j] = score

    # Labels
    provider_labels = [get_user_name(uid) for uid in providers["user_id"]]
    founder_labels = [get_user_name(uid) for uid in founders["user_id"]]

    # Plot
    plt.figure(figsize=(14, 10))
    sns.heatmap(
        matrix,
        cmap="YlGnBu",
        xticklabels=provider_labels,
        yticklabels=founder_labels,
        linewidths=0.5,
        linecolor='gray',
        annot=True,
        fmt=".1f",
        cbar_kws={"label": "Match Score"}
    )
    plt.title("Match Score Heatmap: Founders vs Providers", fontsize=16)
    plt.xlabel("Providers", fontsize=12)
    plt.ylabel("Founders", fontsize=12)
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

if __name__ == "__main__":
    # Load your dataset
    data = pd.read_csv("cleaned_User_Matching_Dataset.csv")

    # Split founders and providers for heatmap and matching
    founders = data[data["user_id"].str.startswith("F")].copy()
    providers = data[data["user_id"].str.startswith("S")].copy()

    # Generate matches
    founder_matches, provider_matches = generate_matches(data)

    # Save match results
    founder_matches.to_csv("founder_top_matches.csv", index=False)
    provider_matches.to_csv("provider_top_matches.csv", index=False)

    # Simple label function for heatmap
    def get_user_name(user_id):
        return user_id  # Replace with actual name logic if available

    # Generate heatmap
    generate_match_heatmap(founders, providers, get_user_name)

