#!/usr/bin/env python
# coding: utf-8

# # Segmenting and Clustering Neighborhoods in the city of Toronto, Canada

# Dowloading all the dependencies

# In[1]:


import numpy as np # library to handle data in a vectorized manner

import pandas as pd # library for data analsysis
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

import json # library to handle JSON files

get_ipython().system("conda install -c conda-forge geopy --yes # uncomment this line if you haven't completed the Foursquare API lab")
from geopy.geocoders import Nominatim # convert an address into latitude and longitude values


import requests # library to handle requests
from pandas.io.json import json_normalize # tranform JSON file into a pandas dataframe

# Matplotlib and associated plotting modules
import matplotlib.cm as cm
import matplotlib.colors as colors

# import k-means from clustering stage
from sklearn.cluster import KMeans

get_ipython().system("conda install -c conda-forge folium=0.5.0 --yes # uncomment this line if you haven't completed the Foursquare API lab")
import folium # map rendering library

print('Libraries imported.')


# Scrape Toronto postcode data from Wikipedia

# In[2]:


url = 'https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M'
wiki = pd.read_html(url)
toronto_df = wiki[0]
toronto_df.head()


# Drop rows where 'Borough' is 'Not assigned'

# In[3]:


toronto_df.drop(toronto_df.loc[toronto_df['Borough']=='Not assigned'].index, inplace=True)
toronto_df.head()


# Replace the 'Not assigned' values in the 'Neighbourhood' column with the 'Borough' value

# In[4]:


toronto_df.Neighbourhood.replace('Not assigned',toronto_df.Borough,inplace=True)


# Check the shape of the dataframe

# In[5]:


toronto_df.shape


# Convert the geospatial data from csv to dataframe

# In[6]:


latlong_df = pd.read_csv('http://cocl.us/Geospatial_data')
latlong_df.head()


# Merging the geospatial data dataframe with the postcode data dataframe

# In[7]:


toronto_latlong_df = toronto_df.merge(latlong_df, on="Postal Code", how="left")
toronto_latlong_df.head()


# Create new datagrame of only neighbourhoods that contain 'Toronto'

# In[8]:


torontov2_df = toronto_latlong_df[toronto_latlong_df['Borough'].str.contains("Toronto")].reset_index(drop=True)


# In[9]:


torontov2_df.shape


# Use geopy library to get the latitude and longitude values of Toronto.

# In[10]:


address = 'Toronto, ON'

geolocator = Nominatim(user_agent="toronto_explorer")
location = geolocator.geocode(address)
latitude = location.latitude
longitude = location.longitude
print('The geograpical coordinate of Toronto are {}, {}.'.format(latitude, longitude))


# Create a map of Toronto with neighborhoods superimposed on top.

# In[11]:


map_toronto = folium.Map(location=[latitude, longitude], zoom_start=10)
for lat, lng, borough, neighborhood in zip(torontov2_df['Latitude'], torontov2_df['Longitude'], torontov2_df['Borough'], torontov2_df['Neighbourhood']):
    label = '{}, {}'.format(neighborhood, borough)
    label = folium.Popup(label, parse_html=True)
    folium.CircleMarker(
        [lat, lng],
        radius=5,
        popup=label,
        color='blue',
        fill=True,
        fill_color='#3186cc',
        fill_opacity=0.7,
        parse_html=False).add_to(map_toronto)  
map_toronto
   


# Defining foursquare credentials

# In[12]:


CLIENT_ID = 'KTLBN10PJAGAA2KUHO22M2MY0NZGEDKWPXJOIBBHDAZWGIXS' # your Foursquare ID
CLIENT_SECRET = '1WVQXWVNKQA0OGMLWGSA40NRD1G2U2TL1IGEULT1MIGEK5EQ' # your Foursquare Secret
VERSION = '20180605' # Foursquare API version

print('Your credentails:')
print('CLIENT_ID: ' + CLIENT_ID)
print('CLIENT_SECRET:' + CLIENT_SECRET)


# Exploring the first neighbourhood in the dataframe

# In[13]:


torontov2_df.loc[0, 'Neighbourhood']


# Get the neighbourhood's lat and long values

# In[14]:


neighborhood_latitude = torontov2_df.loc[0, 'Latitude'] # neighborhood latitude value
neighborhood_longitude = torontov2_df.loc[0, 'Longitude'] # neighborhood longitude value

neighborhood_name = torontov2_df.loc[0, 'Neighbourhood'] # neighborhood name

print('Latitude and longitude values of {} are {}, {}.'.format(neighborhood_name, 
                                                               neighborhood_latitude, 
                                                               neighborhood_longitude))


# Now, let's get the top 100 venues that are in Regent Park, Harbourfront within a radius of 500 meters.
# First, let's create the GET request URL. Name your URL url.

# In[15]:


LIMIT = 100 # limit of number of venues returned by Foursquare API



radius = 500 # define radius



url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
    CLIENT_ID, 
    CLIENT_SECRET, 
    VERSION, 
    neighborhood_latitude, 
    neighborhood_longitude, 
    radius, 
    LIMIT)
url # display URL


# Send the GET request 

# In[16]:


results = requests.get(url).json()
results


# function that extracts the category of the venue

# In[17]:


def get_category_type(row):
    try:
        categories_list = row['categories']
    except:
        categories_list = row['venue.categories']
        
    if len(categories_list) == 0:
        return None
    else:
        return categories_list[0]['name']


# In[18]:


venues = results['response']['groups'][0]['items']
    
nearby_venues = json_normalize(venues) # flatten JSON

# filter columns
filtered_columns = ['venue.name', 'venue.categories', 'venue.location.lat', 'venue.location.lng']
nearby_venues =nearby_venues.loc[:, filtered_columns]

# filter the category for each row
nearby_venues['venue.categories'] = nearby_venues.apply(get_category_type, axis=1)

# clean columns
nearby_venues.columns = [col.split(".")[-1] for col in nearby_venues.columns]

nearby_venues.head()


# And how many venues were returned by Foursquare?

# In[19]:


print('{} venues were returned by Foursquare.'.format(nearby_venues.shape[0]))


# Let's create a function to repeat the same process to all the neighborhoods in Toronto

# In[20]:


def getNearbyVenues(names, latitudes, longitudes, radius=500):
    
    venues_list=[]
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)
            
        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            lat, 
            lng, 
            radius, 
            LIMIT)
            
        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']
        
        # return only relevant information for each nearby venue
        venues_list.append([(
            name, 
            lat, 
            lng, 
            v['venue']['name'], 
            v['venue']['location']['lat'], 
            v['venue']['location']['lng'],  
            v['venue']['categories'][0]['name']) for v in results])

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Neighborhood', 
                  'Neighborhood Latitude', 
                  'Neighborhood Longitude', 
                  'Venue', 
                  'Venue Latitude', 
                  'Venue Longitude', 
                  'Venue Category']
    
    return(nearby_venues)


# Now write the code to run the above function on each neighborhood and create a new dataframe called toronto_venues.

# In[21]:


toronto_venues = getNearbyVenues(names=torontov2_df['Neighbourhood'],
                                   latitudes=torontov2_df['Latitude'],
                                   longitudes=torontov2_df['Longitude']
                                  )


# Let's check the size of the resulting dataframe

# In[22]:


print(toronto_venues.shape)
toronto_venues.head()


# Let's check how many venues were returned for each neighborhood

# In[23]:


toronto_venues.groupby('Neighborhood').count()


# Let's find out how many unique categories can be curated from all the returned venues

# In[24]:


print('There are {} uniques categories.'.format(len(toronto_venues['Venue Category'].unique())))


# ## Analyse each neighbourhood

# In[25]:


# one hot encoding
toronto_onehot = pd.get_dummies(toronto_venues[['Venue Category']], prefix="", prefix_sep="")

# add neighborhood column back to dataframe
toronto_onehot['Neighborhood'] = toronto_venues['Neighborhood'] 

# move neighborhood column to the first column
fixed_columns = [toronto_onehot.columns[-1]] + list(toronto_onehot.columns[:-1])
toronto_onehot = toronto_onehot[fixed_columns]

toronto_onehot.head()


# Next, let's group rows by neighborhood and by taking the mean of the frequency of occurrence of each category

# In[26]:


toronto_grouped = toronto_onehot.groupby('Neighborhood').mean().reset_index()
toronto_grouped


# Let's print each neighborhood along with the top 5 most common venues

# In[27]:


num_top_venues = 5

for hood in toronto_grouped['Neighborhood']:
    print("----"+hood+"----")
    temp = toronto_grouped[toronto_grouped['Neighborhood'] == hood].T.reset_index()
    temp.columns = ['venue','freq']
    temp = temp.iloc[1:]
    temp['freq'] = temp['freq'].astype(float)
    temp = temp.round({'freq': 2})
    print(temp.sort_values('freq', ascending=False).reset_index(drop=True).head(num_top_venues))
    print('\n')


# ### Let's put that into a pandas dataframe
# First, let's write a function to sort the venues in descending order.

# In[28]:


def return_most_common_venues(row, num_top_venues):
    row_categories = row.iloc[1:]
    row_categories_sorted = row_categories.sort_values(ascending=False)
    
    return row_categories_sorted.index.values[0:num_top_venues]


# 
# Now let's create the new dataframe and display the top 10 venues for each neighborhood.
# 

# In[29]:


num_top_venues = 10

indicators = ['st', 'nd', 'rd']

# create columns according to number of top venues
columns = ['Neighborhood']
for ind in np.arange(num_top_venues):
    try:
        columns.append('{}{} Most Common Venue'.format(ind+1, indicators[ind]))
    except:
        columns.append('{}th Most Common Venue'.format(ind+1))

# create a new dataframe
neighborhoods_venues_sorted = pd.DataFrame(columns=columns)
neighborhoods_venues_sorted['Neighborhood'] = toronto_grouped['Neighborhood']

for ind in np.arange(toronto_grouped.shape[0]):
    neighborhoods_venues_sorted.iloc[ind, 1:] = return_most_common_venues(toronto_grouped.iloc[ind, :], num_top_venues)

neighborhoods_venues_sorted.head()


# ## Cluster Neighborhoods

# Run *k*-means to cluster the neighborhood into 5 clusters

# In[30]:


# set number of clusters
kclusters = 5

toronto_grouped_clustering = toronto_grouped.drop('Neighborhood', 1)

# run k-means clustering
kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(toronto_grouped_clustering)

# check cluster labels generated for each row in the dataframe
kmeans.labels_[0:10] 


# In[31]:


# add clustering labels
neighborhoods_venues_sorted.insert(0, 'Cluster Labels', kmeans.labels_)

toronto_merged = torontov2_df

# merge toronto_grouped with toronto_data to add latitude/longitude for each neighborhood
toronto_merged = toronto_merged.join(neighborhoods_venues_sorted.set_index('Neighbourhood'), on='Neighbourhood')

toronto_merged.head() # check the last columns!


# In[ ]:




