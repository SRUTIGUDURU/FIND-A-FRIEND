import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.cluster import AgglomerativeClustering
from collections import Counter
from supabase import create_client, Client
import schedule
import time
import json

# Supabase credentials
supabase_url = 'https://okmzzeoaqkllbzpyynnl.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9rbXp6ZW9hcWtsbGJ6cHl5bm5sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzAxMzE5NzQsImV4cCI6MjA0NTcwNzk3NH0.hpmwUO2UozsTwm0g9cbCR4_Rgr_Go-vRHMPUfi582-g'  # Replace with your actual Supabase key
supabase: Client = create_client(supabase_url, supabase_key)

# Fetch data from the 'questionnaire' table
def fetch_questionnaire_data():
    response = supabase.from_("questionnaire").select("*").execute()
    if response.error:
        print("Error fetching data:", response.error)
        return None
    return pd.DataFrame(response.data)

# Process and cluster data
def process_and_cluster(df):
    # Split the 'hobbies' and 'topics' columns into lists
    df['hobbies'] = df['hobbies'].apply(lambda x: x.split(','))
    df['topics'] = df['topics'].apply(lambda x: x.split(','))

    # Create unique sets for hobbies and topics
    unique_hobbies = set(hobby.strip() for sublist in df['hobbies'] for hobby in sublist)
    unique_topics = set(topic.strip() for sublist in df['topics'] for topic in sublist)

    # Expand 'hobbies' and 'topics' into one-hot encoded columns
    for hobby in unique_hobbies:
        df[hobby] = df['hobbies'].apply(lambda x: 1 if hobby in [h.strip() for h in x] else 0)
    for topic in unique_topics:
        df[topic] = df['topics'].apply(lambda x: 1 if topic in [t.strip() for t in x] else 0)

    df.drop(['hobbies', 'topics'], axis=1, inplace=True)  # Drop original columns

    # Calculate Euclidean distances and similarity scores
    hobbies_distances = euclidean_distances(df[list(unique_hobbies)])
    topics_distances = euclidean_distances(df[list(unique_topics)])
    df['hobbies_similarity'] = 1 / (1 + hobbies_distances.mean(axis=1))
    df['topics_similarity'] = 1 / (1 + topics_distances.mean(axis=1))
    df['combined_similarity'] = (df['hobbies_similarity'] + df['topics_similarity']) / 2

    # Cluster based on combined similarity scores
    num_groups = len(df) // 5
    clustering_data = df[['combined_similarity']]
    agg_cluster = AgglomerativeClustering(n_clusters=num_groups, affinity='euclidean', linkage='ward')
    df['cluster'] = agg_cluster.fit_predict(clustering_data)

    return adjust_group_sizes(df, min_size=4, max_size=6)

# Adjust group sizes if necessary
def adjust_group_sizes(df, min_size=4, max_size=6):
    from random import choice
    group_sizes = Counter(df['cluster'])
    small_groups = [group for group, size in group_sizes.items() if size < min_size]
    large_groups = [group for group, size in group_sizes.items() if size > max_size]

    for group in large_groups:
        while group_sizes[group] > max_size:
            individual_index = choice(df[df['cluster'] == group].index)
            new_group = choice(small_groups)
            df.at[individual_index, 'cluster'] = new_group
            group_sizes[group] -= 1
            group_sizes[new_group] += 1

    return df

# Extract clusters and organize them by email
def extract_clusters(df):
    clusters = df['cluster'].unique()
    grouped_data = {}
    for cluster in clusters:
        grouped_data[f'Group {cluster + 1}'] = df[df['cluster'] == cluster]['email'].tolist()
    return grouped_data

# Validate groups based on similarity threshold
def validate_group_similarity(groups, df):
    valid_groups = {}
    for group_name, members in groups.items():
        similarities = []
        for member in members:
            member_row = df[df['email'] == member].iloc[0]
            for other_member in members:
                if member != other_member:
                    other_member_row = df[df['email'] == other_member].iloc[0]
                    similarity_score = 1 - euclidean_distances(
                        member_row[unique_hobbies.union(unique_topics)].values.reshape(1, -1),
                        other_member_row[unique_hobbies.union(unique_topics)].values.reshape(1, -1)
                    )[0][0]
                    similarities.append(similarity_score)

        if all(sim >= 0.5 for sim in similarities):
            valid_groups[group_name] = members
    return valid_groups

# Save valid groups to the 'groups' table in Supabase
def save_groups_to_supabase(groups):
    for group_name, members in groups.items():
        group_data = {'group_name': group_name, 'members': json.dumps(members)}
        response = supabase.from_("groups").insert([group_data]).execute()
        if response.error:
            print("Error inserting group data:", response.error)

# Main function to run clustering and saving
def run_clustering():
    df = fetch_questionnaire_data()
    if df is not None and not df.empty:
        clustered_df = process_and_cluster(df)
        groups = extract_clusters(clustered_df)
        valid_groups = validate_group_similarity(groups, clustered_df)
        save_groups_to_supabase(valid_groups)

# Schedule the clustering task to run daily at 12:00 PM
schedule.every().day.at("12:00").do(run_clustering)

# Keep the script running to allow scheduled tasks
while True:
    schedule.run_pending()
    time.sleep(60)  # Wait for one minute between checks
