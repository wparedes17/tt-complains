import pandas as pd

def build_survival_dataset(
        drivers_file: str,
        trips_file: str,
        complaints_file: str,
        reference_date: str = "2024-01-01 00:00:00"
) -> pd.DataFrame:
    """
    Build dataset for survival analysis from driver, trip, and complaint data.

    Args:
        drivers_file: Path to CSV with driver data
        trips_file: Path to CSV with trip data
        complaints_file: Path to CSV with complaint data
        reference_date: Reference date for time calculations

    Returns:
        DataFrame with features for survival analysis
    """
    # Load data
    drivers_df = pd.read_csv(drivers_file, sep='|')
    trips_df = pd.read_csv(trips_file, sep='|')
    complaints_df = pd.read_csv(complaints_file, sep='|')

    # Convert datetime columns
    trips_df['start_datetime'] = pd.to_datetime(trips_df['start_datetime'])
    trips_df['end_datetime'] = pd.to_datetime(trips_df['end_datetime'])
    complaints_df['complain_datetime'] = pd.to_datetime(complaints_df['complain_datetime'])
    reference_date = pd.to_datetime(reference_date)

    # Initialize result DataFrame with basic driver features
    result_df = drivers_df[['driver_id', 'experience', 'age', 'sex']].copy()

    # Add quit indicator
    result_df['has_quit'] = (drivers_df['status'] == 'quit').astype(int)

    # Calculate number of complaints per driver
    complaint_counts = complaints_df.groupby('driver_id').size()
    result_df['number_of_complaints'] = result_df['driver_id'].map(complaint_counts).fillna(0)

    # Calculate average inter-complaint time
    def calculate_inter_complaint_time(group):
        if len(group) < 2:
            return pd.NA
        sorted_times = group['complain_datetime'].sort_values()
        time_diffs = sorted_times.diff()
        return time_diffs.mean().total_seconds() / (60 * 60 * 24)  # Convert to days

    inter_complaint_times = complaints_df.groupby('driver_id').apply(calculate_inter_complaint_time)
    result_df['avg_inter_complaint_time'] = result_df['driver_id'].map(inter_complaint_times)

    # Calculate average inter-trip time
    def calculate_inter_trip_time(group):
        if len(group) < 2:
            return pd.NA
        sorted_times = group['start_datetime'].sort_values()
        time_diffs = sorted_times.diff()
        return time_diffs.mean().total_seconds() / (60 * 60 * 24)  # Convert to days

    inter_trip_times = trips_df.groupby('driver_id').apply(calculate_inter_trip_time)
    result_df['avg_inter_trip_time'] = result_df['driver_id'].map(inter_trip_times)

    # Calculate time since last trip
    def get_last_trip_time(group):
        if len(group) == 0:
            return pd.NA
        return group['end_datetime'].max()

    last_trip_times = trips_df.groupby('driver_id').apply(get_last_trip_time)
    result_df['last_trip_datetime'] = result_df['driver_id'].map(last_trip_times)
    result_df['time_since_last_trip'] = (
            (pd.to_datetime(result_df['last_trip_datetime']) - reference_date)
            .dt.total_seconds() / (60 * 60 * 24)  # Convert to days
    )

    # Get most common complaint topic
    def get_most_common_topic(group):
        if len(group) == 0:
            return pd.NA
        return group['predicted_topic'].mode().iloc[0]

    most_common_topics = complaints_df.groupby('driver_id').apply(get_most_common_topic)
    result_df['most_common_complaint_topic'] = result_df['driver_id'].map(most_common_topics)

    # Clean up the dataset
    # Fill NA values with appropriate defaults
    result_df['avg_inter_complaint_time'] = result_df['avg_inter_complaint_time'].fillna(0)
    result_df['avg_inter_trip_time'] = result_df['avg_inter_trip_time'].fillna(0)
    result_df['time_since_last_trip'] = result_df['time_since_last_trip'].fillna(0)
    result_df['most_common_complaint_topic'] = result_df['most_common_complaint_topic'].fillna(-1)

    return result_df
