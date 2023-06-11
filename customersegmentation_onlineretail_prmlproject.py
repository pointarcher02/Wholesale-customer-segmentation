# -*- coding: utf-8 -*-
"""CustomerSegmentation_OnlineRetail_PRMLProject.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1DEB9YnmXi7fchzixmfI0UTuR1OusXk5Z
"""

from google.colab import drive 
drive.mount('/content/drive')

import numpy
import pandas as pd
import warnings
import datetime as dt
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import plotly.express as px
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.decomposition import TruncatedSVD, PCA
from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.tree import DecisionTreeClassifier

"""# Segmenting Customers based upon their buying behaviour and geographical segmenting

## Preprocessing
"""

warnings.filterwarnings('ignore')

df = pd.read_excel("/content/drive/MyDrive/Colab Notebooks/Online Retail.xlsx")
df.head()

"""It took a few minutes to load the data, so we keep a copy as a backup."""

df1 = df

df1.Country.nunique()

df1.Country.unique()

customer_country=df1[['Country','CustomerID']].drop_duplicates()

customer_country.groupby(['Country'])['CustomerID'].aggregate('count').reset_index().sort_values('CustomerID', ascending=False)

"""## United Kingdom

More than 90% of the customers in the data are from United Kingdom, There’s some research indicating that customer clusters vary by geography, so showing the customer types within the country : United Kingdom
"""

df1 = df1.loc[df1['Country'] == 'United Kingdom']

"""Check whether there are missing values in each column.

There are 133600 missing values in CustomerID column, since our analysis is based on customers, we will remove these missing values.
"""

df1.isnull().sum(axis=0)

df1 = df1[pd.notnull(df1['CustomerID'])]
df1.isnull().sum(axis=0)

"""Check the min and max values in Unit price column"""

df1.UnitPrice.min()

df1.Quantity.min()

"""Removing the negative values in Quantity column"""

df1 = df1[(df1['Quantity']>0)]
df1.Quantity.min()

"""After cleaning up, we now deal with 354345 rows and 9 columns"""

df1.shape

df1.info()

"""Checking unique value for each column"""

def unique_counts(df1):
   for i in df1.columns:
       count = df1[i].nunique()
       print(i, ": ", count)
unique_counts(df1)

df1.head()

"""Adding a column for total price"""

df1['TotalPrice'] = df1['Quantity'] * df1['UnitPrice']
df1.head()

"""Find out first and last order date in the data"""

df1['InvoiceDate'].min()

df1['InvoiceDate'].max()

"""Since recency is calculated for a point in time. The last invoice date is 2011-12-09, this is the date we will use to calculate recency."""

NOW = dt.datetime(2011,12,10)

NOW

df1['InvoiceDate'] = pd.to_datetime(df1['InvoiceDate'])

"""Creating a RFM (Recency - Frequency - Monetary Value) table"""

rfmTable = df1.groupby('CustomerID').agg({'InvoiceDate': lambda x: (NOW - x.max()).days, # Recency
                                        'InvoiceNo': lambda x: len(x),      # Frequency
                                        'TotalPrice': lambda x: x.sum()}) # Monetary Value

rfmTable['InvoiceDate'] = rfmTable['InvoiceDate'].astype(int)
rfmTable.rename(columns={'InvoiceDate': 'recency', 
                         'InvoiceNo': 'frequency', 
                         'TotalPrice': 'monetary_value'}, inplace=True)

"""Calculating RFM metrics for each customer"""

rfmTable.head()

"""Interpretation:

CustomerID 12346 has frequency:1, monetary value:$77183.60 and recency:324 days.

CustomerID 12747 has frequency: 103, monetary value: $4196.01 and recency: 1 day

Let's check the details of the first customer.
"""

first_customer = df1[df1['CustomerID']== 12346.0]
first_customer

"""The first customer has shopped only once, bought one item at a huge quantity(74215). The unit price is very low, seems a clearance sale or the customer may be a wholesaler """

(NOW - dt.datetime(2011,1,18)).days==326

"""Splitting metrics into segments by using tertiles, that is dividing 3-quantiles, that is splitting into three equal divisions"""

quantiles = rfmTable.quantile(q=[0.33,0.67])
quantiles

quantiles = quantiles.to_dict()
quantiles

"""Creating a segmented RFM table"""

segmented_rfm = rfmTable

segmented_rfm

"""Lowest recency, highest frequency and monetary can be considered as the best customers for our company """

def RScore(x,p,d):
    if x <= d[p][0.33]:
        return 1
    elif x <= d[p][0.67]:
        return 2
    else:
        return 3
    
def FMScore(x,p,d):
    if x <= d[p][0.33]:
        return 3
    elif x <= d[p][0.67]:
        return 2
    else:
        return 1

segmented_rfm['r_quartile'] = segmented_rfm['recency'].apply(RScore, args=('recency',quantiles,))
segmented_rfm['f_quartile'] = segmented_rfm['frequency'].apply(FMScore, args=('frequency',quantiles,))
segmented_rfm['m_quartile'] = segmented_rfm['monetary_value'].apply(FMScore, args=('monetary_value',quantiles,))

"""Add segment numbers to the RFM table"""

segmented_rfm.head()

"""RFM segments split your customer base into an imaginary 3D cube. It is hard to visualize. However, we can sort it out."""

segmented_rfm['RFMScore'] = segmented_rfm.r_quartile.map(str) \
                            + segmented_rfm.f_quartile.map(str) \
                            + segmented_rfm.m_quartile.map(str)
segmented_rfm.head()

"""Apparently, the first customer is not our best customer at all.

Here is top 10 of our best customers!

Loyal and Regular Customers with high demands of expensive goods
"""

segmented_rfm[segmented_rfm['RFMScore']=='111'].sort_values('monetary_value', ascending=False).head(10)

"""Writing a function to segment customer types of each country given the segmented rfm table as input and classifying each customer type based on the tertiles/quantiles"""

def customer_segmentation_rfm(rfm):
  rfm['Label'] = -1
  rfm['Customer Type'] = 's'
  rfm_arr_score = rfm['RFMScore'].values
  rfm_arr_label = rfm['Label'].values
  rfm_arr_ct = rfm['Customer Type'].values
  for i in range(len(rfm_arr_score)):
    rfm_arr_score[i] = int(rfm_arr_score[i])

  for i in range(len(rfm_arr_score)):
    if (rfm_arr_score[i] == 231 or rfm_arr_score[i]== 131 or rfm_arr_score[i]== 331) :
      rfm_arr_label[i] = 1
      rfm_arr_ct[i] = 'WholeSaler or Corporate Gifter'
    elif (rfm_arr_score[i] == 113 or rfm_arr_score[i]== 213) :
      rfm_arr_label[i] = 2
      rfm_arr_ct[i] = 'Regular customer with interest towards affordable gifting' 
    elif (rfm_arr_score[i] == 111 or rfm_arr_score[i]== 211) :
      rfm_arr_label[i] = 3
      rfm_arr_ct[i] = 'Regular Customer with high demand of expensive gifts'
    elif rfm_arr_score[i] == 122 or rfm_arr_score[i]== 222 :
      rfm_arr_label[i] = 4
      rfm_arr_ct[i] = 'Moderate Customer with moderate level demands'
    elif rfm_arr_score[i] == 133 or rfm_arr_score[i] == 233 :
      rfm_arr_label[i] = 5
      rfm_arr_ct[i] = 'Potential emerging customer, inprofitable right now but can be profitable in coming times '   
    elif rfm_arr_score[i] == 212 or rfm_arr_score[i]== 112 :
      rfm_arr_label[i] = 6
      rfm_arr_ct[i] = 'Regular customer with high demand of average price gifts'
    elif rfm_arr_score[i] == 132 or rfm_arr_score[i]== 232 or rfm_arr_score[i]== 123 or rfm_arr_score[i]== 223 :
      rfm_arr_label[i] = 7
      rfm_arr_ct[i] = 'Emerging Customer, profitable with moderate buying demands '
    elif rfm_arr_score[i] == 121 or rfm_arr_score[i]== 221 :
      rfm_arr_label[i] = 8
      rfm_arr_ct[i] = 'Retailers or the ones with shops in city who buy weekly or monthly to run their shops'
    else :
      rfm_arr_label[i] = 9
      rfm_arr_ct[i] = 'Nearly lost or inactive customers, not bought anything since a long time'

  return rfm

customer_segmentation_rfm(segmented_rfm)

"""Writing a function to plot a 3d scatter graph given the segmented rfm table with labels and clustering similar customers """

def plot(segmented_rfm):
  # Separate labels and features
  labels = segmented_rfm["Label"]
  features = segmented_rfm.drop(columns = ['Label', 'recency', 'frequency', 'monetary_value', 'RFMScore', 'Customer Type'])

  kmeans = KMeans(n_clusters=labels.nunique(), random_state=42)
  kmeans.fit(features)
  predicted_labels = kmeans.labels_

  fig = px.scatter_3d(features, x=features.columns[0], y=features.columns[1], z=features.columns[2], color=predicted_labels)

  # Creating a scatter plot of the features with different colors for each predicted label
  return fig.show()

plot(segmented_rfm)

"""## Germany"""

def customer_segmentation(country,df):
  df_seg = df.copy()
  df_seg = df_seg.loc[df_seg['Country'] == country ]
  if df_seg.isnull().sum(axis=0).CustomerID > 0 : 
    df_seg = df_seg[pd.notnull(df_seg['CustomerID'])]
  if df_seg.Quantity.min() < 0 :
    df_seg = df_seg[df_seg['Quantity'] > 0]
  #print(df_seg.shape)
  #print(df_seg.info())
  #print(unique_counts(df_seg))
  df_seg['TotalPrice'] = df_seg['Quantity'] * df_seg['UnitPrice']
  #print(df_seg.head())
  df_seg['InvoiceDate'] = pd.to_datetime(df_seg['InvoiceDate'])
  rfmtable_seg = df_seg.groupby('CustomerID').agg({'InvoiceDate': lambda x: (NOW - x.max()).days, # Recency
                                        'InvoiceNo': lambda x: len(x),      # Frequency
                                        'TotalPrice': lambda x: x.sum()}) # Monetary Value

  rfmtable_seg['InvoiceDate'] = rfmtable_seg['InvoiceDate'].astype(int)
  rfmtable_seg.rename(columns={'InvoiceDate': 'recency', 
                         'InvoiceNo': 'frequency', 
                         'TotalPrice': 'monetary_value'}, inplace=True)
  quantiles_seg = rfmtable_seg.quantile(q=[0.33, 0.67])
  quantiles_seg = quantiles_seg.to_dict()
  #print(quantiles_seg)
  segmented_rfm_seg = rfmtable_seg
  segmented_rfm_seg['r_quartile'] = segmented_rfm_seg['recency'].apply(RScore, args=('recency',quantiles,))
  segmented_rfm_seg['f_quartile'] = segmented_rfm_seg['frequency'].apply(FMScore, args=('frequency',quantiles,))
  segmented_rfm_seg['m_quartile'] = segmented_rfm_seg['monetary_value'].apply(FMScore, args=('monetary_value',quantiles,))
  segmented_rfm_seg['RFMScore'] = segmented_rfm_seg.r_quartile.map(str) \
                            + segmented_rfm_seg.f_quartile.map(str) \
                            + segmented_rfm_seg.m_quartile.map(str)
  return segmented_rfm_seg.head()

segmented_rfm_germany = customer_segmentation('Germany', df)
segmented_rfm_germany

customer_segmentation_rfm(segmented_rfm_germany)

plot(segmented_rfm_germany)

"""## France"""

segmented_rfm_france = customer_segmentation('France', df)

segmented_rfm_france

segmented_rfm_france_new = customer_segmentation_rfm(segmented_rfm_france)

segmented_rfm_france_new

plot(segmented_rfm_france_new)

"""## Plots for Rest of the Countries"""

df_copy = df.copy()
df_copy = df_copy[df_copy['Country'] != 'Hong Kong']

countries = df_copy.Country.unique()


for i in range(len(countries)):
  
  segmented_rfm_country=customer_segmentation(countries[i],df_copy)
  
  segmented_rfm_country_new = customer_segmentation_rfm(segmented_rfm_country)
  print(countries[i])
  
  plot(segmented_rfm_country_new)

"""# Implementing classifiers for Segmentation, with labels being countries

## PreProcessing
"""

segment_df = df.copy()

segment_df

segment_df.isnull().sum()

#dropping the 'lower' column since it contains many null values and hence it is of no use to us for the classification

segment_df_2 = segment_df.drop(columns = ['lower'])

segment_df_2.isnull().sum()

segment_df_2 = segment_df_2[pd.notnull(segment_df_2['CustomerID'])]

segment_df_2.isnull().sum()

# Remove cancelled orders
segment_df_2 = segment_df_2[segment_df_2["Quantity"] > 0]

# Convert the InvoiceDate column to datetime
segment_df_2["InvoiceDate"] = pd.to_datetime(segment_df_2["InvoiceDate"])

# Create a TotalPrice column
segment_df_2["TotalPrice"] = segment_df_2["Quantity"] * segment_df_2["UnitPrice"]

rfm_segment_cust = segment_df_2.groupby('CustomerID').agg({'InvoiceDate': lambda x: (NOW - x.max()).days, # Recency
                                        'InvoiceNo': lambda x: len(x),      # Frequency
                                        'TotalPrice': lambda x: x.sum(),    # Monetary Value
                                        'Country' : lambda x: x }) 
rfm_segment_cust['InvoiceDate'] = rfm_segment_cust['InvoiceDate'].astype(int)
rfm_segment_cust.rename(columns={'InvoiceDate': 'recency', 
                         'InvoiceNo': 'frequency', 
                         'TotalPrice': 'monetary_value'}, inplace=True)

rfm_segment_cust

rfm_segment_cust['Country'].values

for i in range(len(rfm_segment_cust['Country'].values)) : 
  if type(rfm_segment_cust['Country'].values[i]) == str:
    continue
  else : 
    for j in range(len(rfm_segment_cust['Country'].values[i])) : 
      rfm_segment_cust['Country'].values[i] = rfm_segment_cust['Country'].values[i][j]
      break

rfm_segment_cust

rfm_segment_cust.nunique()

X_train, X_test, y_train, y_test = train_test_split(
    rfm_segment_cust[["recency", "frequency", "monetary_value"]],
    rfm_segment_cust["Country"],
    test_size=0.2,
    random_state=42
)

"""## Random Forest Classifier"""

rfc = RandomForestClassifier(n_estimators=100, random_state=42)
rfc.fit(X_train, y_train)

y_pred = rfc.predict(X_test)

# Evaluating the model's performance
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Precision:", precision_score(y_test, y_pred, average="weighted"))
print("Recall:", recall_score(y_test, y_pred, average="weighted"))
print("F1 Score:", f1_score(y_test, y_pred, average="weighted"))

customer_types = rfc.predict(rfm_segment_cust[["recency", "frequency", "monetary_value"]])
rfm_segment_cust["CustomerType"] = customer_types

customer_type_counts = rfm_segment_cust["CustomerType"].value_counts()
customer_type_counts.plot(kind="bar", title="Customer Types")

"""## SVD and KNN Classifier"""

svd = TruncatedSVD(n_components=2, random_state=42)
X_train_svd = svd.fit_transform(X_train)
X_test_svd = svd.transform(X_test)

knn = KNeighborsClassifier()
knn.fit(X_train_svd, y_train)
knn_y_pred = knn.predict(X_test_svd)
knn_accuracy = accuracy_score(y_test, knn_y_pred)
knn_precision = precision_score(y_test, knn_y_pred, average='weighted')
knn_recall = recall_score(y_test, knn_y_pred, average='weighted')
knn_f1_score = f1_score(y_test, knn_y_pred, average='weighted')

print("\nSVD and KNN Classifier:")
print("Accuracy:", knn_accuracy)
print("Precision Score:", knn_precision)
print("Recall:", knn_recall)
print("F1 Score:", knn_f1_score)

"""## PCA and Decision Tree Classifier"""

pca = PCA(n_components=2, random_state=42)
X_train_pca = pca.fit_transform(X_train)
X_test_pca = pca.transform(X_test)

dtc = DecisionTreeClassifier(random_state=42)
dtc.fit(X_train_pca, y_train)
dtc_y_pred = dtc.predict(X_test_pca)
dtc_accuracy = accuracy_score(y_test, dtc_y_pred)
dtc_precision = precision_score(y_test, dtc_y_pred, average='weighted')
dtc_recall = recall_score(y_test, dtc_y_pred, average='weighted')
dtc_f1_score = f1_score(y_test, dtc_y_pred, average='weighted')

print("\nPCA and Decision Tree Classifier:")
print("Accuracy:", dtc_accuracy)
print("Precision Score:", dtc_precision)
print("Recall:", dtc_recall)
print("F1 Score:", dtc_f1_score)

"""## LDA and KNN Classifier"""

lda = LinearDiscriminantAnalysis(n_components=2)
X_train_lda = lda.fit_transform(X_train, y_train)
X_test_lda = lda.transform(X_test)

knn_lda = KNeighborsClassifier()
knn_lda.fit(X_train_lda, y_train)
knn_lda_y_pred = knn_lda.predict(X_test_lda)
knn_lda_accuracy = accuracy_score(y_test, knn_lda_y_pred)
knn_lda_precision = precision_score(y_test, knn_lda_y_pred, average='weighted')
knn_lda_recall = recall_score(y_test, knn_lda_y_pred, average='weighted')
knn_lda_f1_score = f1_score(y_test, knn_lda_y_pred, average='weighted')

print("\nLDA and KNN Classifier:")
print("Accuracy:", knn_lda_accuracy)
print("Precision Score:", knn_lda_precision)
print("Recall:", knn_lda_recall)
print("F1 Score:", knn_lda_f1_score)