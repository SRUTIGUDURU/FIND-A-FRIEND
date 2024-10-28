import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.cluster import AgglomerativeClustering
from collections import Counter
from supabase import create_client, Client
import schedule
import time

# Supabase credentials
supabase_url = 'https://okmzzeoaqkllbzpyynnl.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9rbXp6ZW9hcWtsbGJ6cHl5bm5sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzAxMzE5NzQsImV4cCI6MjA0NTcwNzk3NH0.hpmwUO2UozsTwm0g9cbCR4_Rgr_Go-vRHMPUfi582-g'  # Replace with your Supabase key
supabase: Client = create_client(supabase_url, supabase_key)

# Global variables for unique hobbies and topics
unique_hobbies = set()
unique_topics = set()

# Fetch data from the 'questionnaire' table
def fetch_questionnaire_data():
    response = supabase.from_("questionnaire").select("*").execute()
    if response.error:
        print("Error fetching data:", response.error)
        return None
    return pd.DataFrame(response.data)

# Process and cluster data
def process_and_cluster(df):
    global unique_hobbies, unique_topics  # Declare global variables

    # Split the 'hobbies' and 'topics' columns into lists
    df['hobbies'] = df['hobbies'].apply(lambda x: x.split(','))
    df['topics'] = df['topics'].apply(lambda x: x.split(','))

    # Expand 'hobbies' column into individual hobby columns
    unique_hobbies = set(hobby.strip() for sublist in df['hobbies'] for hobby in sublist)
    for hobby in unique_hobbies:
        df[hobby] = df['hobbies'].apply(lambda x: 1 if hobby in [h.strip() for h in x] else 0)

    # Expand 'topics' column into individual topic columns
    unique_topics = set(topic.strip() for sublist in df['topics'] for topic in sublist)
    for topic in unique_topics:
        df[topic] = df['topics'].apply(lambda x: 1 if topic in [t.strip() for t in x] else 0)

    # Drop the original 'hobbies' and 'topics' columns
    df.drop(['hobbies', 'topics'], axis=1, inplace=True)

    # Calculate Euclidean distance
    def calculate_euclidean_distance(df, columns):
        distance_matrix = euclidean_distances(df[columns])
        similarity_matrix = 1 / (1 + distance_matrix)  # Convert distance to similarity
        return pd.DataFrame(similarity_matrix, index=df.index, columns=df.index)

    # Calculate distances for hobbies and topics
    hobbies_euclidean = calculate_euclidean_distance(df, list(unique_hobbies))
    topics_euclidean = calculate_euclidean_distance(df, list(unique_topics))

    # Euclidean similarity scores to dataframe
    df['hobbies_euclidean'] = hobbies_euclidean.mean(axis=1)
    df['topics_euclidean'] = topics_euclidean.mean(axis=1)

    # Combine similarity scores from hobbies and topics
    df['combined_similarity'] = (df['hobbies_euclidean'] + df['topics_euclidean']) / 2

    # Drop rows with NaN values if any
    df.dropna(subset=['combined_similarity'], inplace=True)

    # Prepare data for clustering
    clustering_data = df[['combined_similarity']]

    # Define the number of clusters based on group size constraints
    num_groups = len(df) // 5  # Average group size is 5

    # Agglomerative Clustering
    agg_cluster = AgglomerativeClustering(n_clusters=num_groups, affinity='euclidean', linkage='ward')
    df['cluster'] = agg_cluster.fit_predict(clustering_data)

    # Adjust group sizes
    df = adjust_group_sizes(df)

    return df

# Function to adjust group sizes
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

# Extract clusters and return names
def extract_clusters(df):
    clusters = df['cluster'].unique()
    grouped_data = {}
    for cluster in clusters:
        grouped_data[f'Group {cluster + 1}'] = df[df['cluster'] == cluster]['email'].tolist()  # Use email or any unique identifier
    return grouped_data

# Validate group similarity before saving
def validate_group_similarity(groups, df):
    valid_groups = {}
    for group_name, members in groups.items():
        similarities = []
        for member in members:
            member_row = df[df['email'] == member].iloc[0]
            # Calculate similarity with all other members in the group
            for other_member in members:
                if member != other_member:
                    other_member_row = df[df['email'] == other_member].iloc[0]
                    similarity_score = 1 - euclidean_distances(
                        member_row[list(unique_hobbies).union(unique_topics)].values.reshape(1, -1),
                        other_member_row[list(unique_hobbies).union(unique_topics)].values.reshape(1, -1)
                    )[0][0]  # Calculate the similarity score
                    similarities.append(similarity_score)

        # Check if any similarity score is below 50%
        if all(sim >= 0.5 for sim in similarities):
            valid_groups[group_name] = members
            
    return valid_groups

# Save the groups into the new 'groups' table
def save_groups_to_supabase(groups):
    for group_name, members in groups.items():
        group_data = {'group_name': group_name, 'members': members}
        response = supabase.from_("groups").insert([group_data]).execute()
        if response.error:
            print("Error inserting group data:", response.error)

# Main function to run the clustering and saving
def run_clustering():
    df = fetch_questionnaire_data()
    if df is not None:
        clustered_df = process_and_cluster(df)
        groups = extract_clusters(clustered_df)
        
        # Validate groups based on similarity
        valid_groups = validate_group_similarity(groups, clustered_df)

        # Save valid groups to Supabase
        save_groups_to_supabase(valid_groups)

# Schedule the clustering to run at 12 PM every day
schedule.every().day.at("12:00").do(run_clustering)

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(60)  # Wait for one minute
