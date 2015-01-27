import pandas as pd
import matplotlib.pyplot as plt
import urllib2

"""
This program reads in a csv file containing census data on Northamptonshire county in the UK. 
It then plots the population data according to gender, gender by age range, and total population by age range.
Two figure files will be output to the directory specified in the variable plot_path.
"""

# the original populaton data file can be found at http://www.northamptonshireanalysis.co.uk/dataviews/view?viewId=151
# at the above URL under 'Geo-Types' choose the csv for 'County'

# where to save the figure files
plot_path = "C:\\Users\mcassar\Desktop\Coursolve project\\"

url = 'http://www.northamptonshireanalysis.co.uk/data/csv?viewId=151&geoId=28&subsetId=&viewer=CSV'
response = urllib2.urlopen(url)

#pop_file = "C:\\Users\\mcassar\\Desktop\\coursolve project\\council_pop.csv" 
#df_pop = pd.read_csv(pop_file)

df_pop = pd.read_csv(response)
# remove rows not corresponding to Northamptonshire population
df_pop = df_pop[0:1]

# these ranges match what is given in the data file
age_ranges = ['0-4', '5-9', '10-14', '15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50-54',
            '55-59', '60-64', '65-69', '70-74', '75-79', '80-84', '85-89', '90']  # should be 90+ but that kept giving an error


# create total population by gender dataframe
df_pop_male_female = df_pop[['Total Resident Population Persons all ages Male(2011)', 'Total Resident Population Persons All Ages Female(2011)']]
df_pop_male_female.columns = ['Male', 'Female']
df_pop_male_female_percent = df_pop_male_female / df_pop.values[0,2] #dividing by total population

# generate bar plots for total population by gender
fig, axes = plt.subplots(1,2)
df_pop_male_female.transpose().plot(kind='bar', ax=axes[0], color=['b', 'y'], legend=False, title='Actual Value') # need the transpose because the bins are the age ranges and these need to be the rows not columns
df_pop_male_female_percent.transpose().plot(kind='bar', ax=axes[1], color=['b', 'y'], legend=False, title='Percent of Total')
plt.suptitle("Northamptonshire Population by Gender (2011)", size=16)
plt.subplots_adjust(top=0.85, bottom=0.15) # adjust spacing so subplot titles are farther from main title
#plt.savefig(plot_path + 'County_population_gender.png')


# segment the data by total population by age range (need to use 'Total(2011)' to do this as every column uses just 'Total'
total_cols = [col for col in df_pop.columns if 'Total(2011)' in col] 
df_pop_total = df_pop[total_cols]  # select only the column names with 'Male' in the title
total_pop = df_pop_total.values[0,0]
df_pop_total_by_age = df_pop_total.drop(df_pop_total.columns[[0]], axis=1)
df_pop_total_by_age.columns = age_ranges
df_pop_total_by_age_percent = df_pop_total_by_age / total_pop # get % pop by age by dividing by total population


# segment the data by male and age range
male_cols = [col for col in df_pop.columns if 'Male' in col] 
df_pop_male = df_pop[male_cols]  # select only the column names with 'Male' in the title
total_male_pop = df_pop_male.values[0,0]
df_pop_male_by_age = df_pop_male.drop(df_pop_male.columns[[0]], axis=1) # get rid of total male population column
df_pop_male_by_age.columns = age_ranges
df_pop_male_by_age_percent = df_pop_male_by_age / total_male_pop # get % pop by age by dividing by total male pop


# segment the data by female and age range
female_cols = [col for col in df_pop.columns if 'Female' in col] 
df_pop_female = df_pop[female_cols]  # select only the column names with 'Female' in the title
total_female_pop = df_pop_female.values[0,0]
df_pop_female_by_age = df_pop_female.drop(df_pop_female.columns[[0]], axis=1) # get rid of total female population column
df_pop_female_by_age.columns = age_ranges
df_pop_female_by_age_percent = df_pop_female_by_age / total_female_pop # get % pop by age by dividing by total female pop


# generate bar plots for total population, total male population, and female population by age range
fig, axes = plt.subplots(3,2)

ax = df_pop_total_by_age.transpose().plot(kind='bar', ax = axes[0,0], legend=False, title='Count')  
df_pop_total_by_age_percent.transpose().plot(kind='bar', ax=axes[0,1], legend=False, title='Percent')

ax1 = df_pop_male_by_age.transpose().plot(kind='bar', ax = axes[1,0], legend=False)  
df_pop_male_by_age_percent.transpose().plot(kind='bar', ax=axes[1,1], legend=False)

ax2 = df_pop_female_by_age.transpose().plot(kind='bar', ax = axes[2,0], legend=False)  
df_pop_female_by_age_percent.transpose().plot(kind='bar', ax=axes[2,1], legend=False)

plt.suptitle("Northamptonshire Population by Age Range (2011)", size=16)
plt.subplots_adjust(top=0.87, left=0.15, hspace=0.4) # adjust spacing b/w subplots and so so subplot titles are farther from main title

ax.set_ylabel('Total')
ax1.set_ylabel('Male')
ax2.set_ylabel('Female')

#plt.savefig(plot_path + 'County_population_gender_age.png')
plt.show()
