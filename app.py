import streamlit as st
import pandas as pd
import re  # Add this import at the top of your file
import requests
import os

def filter_chunk_on_keywords(chunk, keyword, negative_keywords):
    # Filter based on keyword
    keywords = keyword.split(',')
    filtered_chunk = chunk[chunk['name'].str.contains('|'.join(keywords), case=False)]
    
    # If negative_keywords is a string, split it into a list
    if isinstance(negative_keywords, str):
        negative_keywords = [kw.strip() for kw in negative_keywords.split(',')]
    
    # Filter out negative keywords
    for neg_keyword in negative_keywords:
        neg_keyword = neg_keyword.strip()  # Remove leading/trailing whitespace
        if not neg_keyword:  # Skip empty strings
            continue
        try:
            filtered_chunk = filtered_chunk[~filtered_chunk['name'].str.contains(neg_keyword, case=False)]
        except re.error as e:
            # Uncomment this in your environment if you're using Streamlit
            # st.write(f"Error with negative keyword '{neg_keyword}': {e}")
            pass  # placeholder for the above commented code
            
    return filtered_chunk

def download_dataset(url, filename):
    # Send a HTTP request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Write the contents of the response to a file
        with open(filename, 'wb') as file:
            file.write(response.content)
    else:
        print(f"Failed to download file: {response.status_code}")

def calculate_total_matches(keyword, negative_keywords):
    # Initialize a counter for the matches
    total_matches = 0

    # Initialize a progress bar
    progress_bar = st.progress(0)

    # Create a placeholder for the ongoing total
    total_placeholder = st.empty()

    # Read the CSV in chunks (for better performance with large files)
    chunksize = 10000  # You can adjust this value based on your dataset
    total_size = sum(1 for row in open('results_10M_train.csv', 'r'))

    for i, chunk in enumerate(pd.read_csv('results_10M_train.csv', chunksize=chunksize)):
        # Filter based on keyword
        keywords = keyword.split(',')

        # Filter based on keyword
        filtered_chunk = filter_chunk_on_keywords(chunk, keyword, negative_keywords)

        # Add the number of matches in this chunk to the total
        total_matches += len(filtered_chunk)

        # Update the ongoing total
        total_placeholder.text(f"Ongoing total matches: {total_matches}")

        # Update the progress bar
        progress_bar.progress(min((i * chunksize) / total_size, 1.0))

    # Complete the progress bar
    progress_bar.progress(1.0)

    return total_matches

def search_videos(keyword, negative_keywords, start=0):
    # Create an empty DataFrame for storing results
    results = pd.DataFrame()

    # Read the CSV in chunks (for better performance with large files)
    chunksize = 1000  # You can adjust this value based on your dataset
    for chunk in pd.read_csv('results_10M_train.csv', chunksize=chunksize):
        # Filter based on keyword
        filtered_chunk = filter_chunk_on_keywords(chunk, keyword, negative_keywords)
        
        # Append the filtered results to the results DataFrame
        results = pd.concat([results, filtered_chunk])
        
        # If we have 10 or more results, break
        if len(results) >= start + 50:
            break

    # Return the next 10 results
    return results.iloc[start:start+50]

def display_videos(results):
    if len(results) > 0:
        st.write(f"Displaying {len(results)} videos.")
        
        # Display videos
        for _, row in results.iterrows():
            
            st.write(row['name'])
            st.video(row['contentUrl'])
            st.markdown('***')
    else:
        st.write("No more videos found for the given keyword.")

def create_next_button(location):
    col1, col2, col3 = st.columns([1,5,1])

    with col3:
        if st.button('Next', key=f'next-button-{location}', type="primary"):
            st.session_state.start += 50  # Increase the start index by 10
            st.session_state.results = search_videos(keyword, negative_keywords, st.session_state.start)
            st.experimental_rerun()

def download_matching_rows(keyword, negative_keywords, filename):
    # Create an empty DataFrame for storing results
    results = pd.DataFrame()

    # Read the CSV in chunks (for better performance with large files)
    chunksize = 1000  # You can adjust this value based on your dataset
    for chunk in pd.read_csv('results_10M_train.csv', chunksize=chunksize):
        # Filter based on keyword
        filtered_chunk = filter_chunk_on_keywords(chunk, keyword, negative_keywords)
        
        # Append the filtered results to the results DataFrame
        results = pd.concat([results, filtered_chunk])

    # Append .csv to filename if not already there
    if not filename.endswith('.csv'):
        filename += '.csv'

    # Write all results to a CSV file
    results.to_csv(filename, index=False)

if 'start' not in st.session_state:
    st.session_state.start = 0
    st.session_state.results = pd.DataFrame()


if not os.path.isfile('results_10M_train.csv'):    
    st.write('Dataset not found in the current directory.')    
    if st.button('Download Dataset'):
        download_dataset('http://www.robots.ox.ac.uk/~maxbain/webvid/results_10M_train.csv', 'results_10M_train.csv')
        st.success('Dataset downloaded successfully.')
        st.experimental_rerun()
    st.markdown('***')

else:

    with st.sidebar:

        st.title('Video Searcher')

        # User input
        keyword = st.text_input('Enter keywords:')

        negative_keywords = st.text_area('Enter negative keywords:')

        col1, col2, col3 = st.columns([2,2,2])

        with col1:
            if st.button('Search'):
                st.session_state.start = 0  # Reset the start index when a new search is performed
                st.session_state.results = search_videos(keyword, negative_keywords, st.session_state.start)

        with col2:
            if st.session_state.start != 0:
                if st.button('Update search'):
                    st.session_state.results = search_videos(keyword, negative_keywords, st.session_state.start)
            else:
                st.write('')

        st.markdown('***')

        if st.button('Calculate total matches'):
            total_matches = calculate_total_matches(keyword, negative_keywords)
            st.success(f"Total matches: {total_matches}")

        st.markdown('***')

        filename = st.text_input('Enter filename for download:',value='results')

        if st.button('Download matching rows'):
            download_matching_rows(keyword, negative_keywords, filename + '.csv')
            st.success(f"Downloaded {filename}.csv")

            
    

    if st.session_state.results is not None:

        create_next_button('top')

        st.write(f"Displaying {len(st.session_state.results)} videos.")
        for _, row in st.session_state.results.iterrows():
            st.write(row['name'])
            st.video(row['contentUrl'])

        create_next_button('bottom')


