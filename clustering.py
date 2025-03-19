import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.cluster import AgglomerativeClustering
from collections import Counter
from sqlalchemy import create_engine, Column, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import schedule
import time
import os

# Database connection (PostgreSQL on Neon/Railway)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@host:port/dbname")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define User model
class User(Base):
    __tablename__ = "questionnaire"
    email = Column(String, primary_key=True, index=True)
    hobbies = Column(Text)
    topics = Column(Text)
    gender = Column(String)
    year = Column(String)
    purpose = Column(Text)

# Define Groups model
class Group(Base):
    __tablename__ = "groups"
    id = Column(String, primary_key=True, index=True)
    group_name = Column(String, index=True)
    email = Column(Text)

# Create tables
Base.metadata.create_all(bind=engine)

# Fetch questionnaire data
def fetch_questionnaire_data(db: Session):
    users = db.query(User).all()
    if not users:
        return None
    return pd.DataFrame([{column: getattr(user, column) for column in User.__table__.columns.keys()} for user in users])

# Process and cluster data
def process_and_cluster(df):
    df['hobbies'] = df['hobbies'].apply(lambda x: x.split(','))
    df['topics'] = df['topics'].apply(lambda x: x.split(','))

    unique_hobbies = set(hobby.strip() for sublist in df['hobbies'] for hobby in sublist)
    unique_topics = set(topic.strip() for sublist in df['topics'] for topic in sublist)

    for hobby in unique_hobbies:
        df[hobby] = df['hobbies'].apply(lambda x: 1 if hobby in [h.strip() for h in x] else 0)
    for topic in unique_topics:
        df[topic] = df['topics'].apply(lambda x: 1 if topic in [t.strip() for t in x] else 0)

    df = pd.get_dummies(df, columns=['gender', 'year'], drop_first=True)
    df.drop(['hobbies', 'topics'], axis=1, inplace=True)

    hobbies_distances = euclidean_distances(df[list(unique_hobbies)])
    topics_distances = euclidean_distances(df[list(unique_topics)])
    df['hobbies_similarity'] = 1 / (1 + hobbies_distances.mean(axis=1))
    df['topics_similarity'] = 1 / (1 + topics_distances.mean(axis=1))
    df['combined_similarity'] = (df['hobbies_similarity'] + df['topics_similarity']) / 2

    clustering_data = df.drop(columns=['email', 'purpose', 'hobbies_similarity', 'topics_similarity', 'combined_similarity'])
    num_groups = len(df) // 5
    agg_cluster = AgglomerativeClustering(n_clusters=num_groups, affinity='euclidean', linkage='ward')
    df['cluster'] = agg_cluster.fit_predict(clustering_data)

    return adjust_group_sizes(df, min_size=4, max_size=6)

# Adjust group sizes
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

# Extract clusters
def extract_clusters(df):
    clusters = df['cluster'].unique()
    grouped_data = {}
    for cluster in clusters:
        grouped_data[f'Group {cluster + 1}'] = df[df['cluster'] == cluster]['email'].tolist()
    return grouped_data

# Save valid groups
def save_groups(db: Session, groups):
    for group_name, members in groups.items():
        email_list = ', '.join(members)
        group_data = Group(group_name=group_name, email=email_list)
        db.add(group_data)
    db.commit()

# Main clustering function
def run_clustering():
    db = SessionLocal()
    df = fetch_questionnaire_data(db)
    if df is not None and not df.empty:
        clustered_df = process_and_cluster(df)
        groups = extract_clusters(clustered_df)
        save_groups(db, groups)
    db.close()

# Schedule clustering daily
schedule.every().day.at("12:00").do(run_clustering)

while True:
    schedule.run_pending()
    time.sleep(60)


