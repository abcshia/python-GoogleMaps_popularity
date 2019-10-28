import numpy as np
import pandas as pd
import os,inspect
import pickle
import googlemaps
import gmplot

# Get this current script file's directory:
loc = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# Set working directory
os.chdir(loc)

# to avoid tk crash
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors


## Fetch weekly popularity data

# Set driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

# Chrome
from selenium.webdriver.chrome.options import Options
driverPath = r'C:\Users\James\OneDrive\PythonFiles\packages\selenium\WebDrivers\chromedriver.exe'
chrome_options = Options()
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--incognito")
# chrome_options.add_argument("--window-size=1920x1080")
driver = webdriver.Chrome(chrome_options=chrome_options, executable_path = driverPath)





# search key words
search_words = 'Recreational Sports Facility'#'noodles fresh'#'Monterey Market'#'Grégoire Restaurant' #'daimo'#'Asian Pearl Seafood Restaurant'

# get search results from google maps
html_url = 'https://maps.google.com'
driver.get(html_url)
WebDriverWait(driver,60).until(EC.presence_of_element_located((By.ID, 'searchboxinput')))

searchbox = driver.find_element_by_id('searchboxinput')
searchbox.send_keys(search_words)
# searchbox.submit()
searchbutton = driver.find_element_by_id('searchbox-searchbutton')
searchbutton.click()


# driver.get(html_url)
# wait to load page
WebDriverWait(driver,60).until(EC.presence_of_element_located((By.CLASS_NAME, 'section-popular-times')))



# Get weekly data:
num2dayofweek = {1:'Monday',
                 2:'Tuesday',
                 3:'Wednesday',
                 4:'Thursday',
                 5:'Friday',
                 6:'Saturday',
                 7:'Sunday'
                }

pop_sec = driver.find_element_by_class_name('section-popular-times')
buttons = pop_sec.find_elements_by_tag_name('button')
for button in buttons:
    if button.get_attribute('class') == 'section-popular-times-arrow-right noprint':
        next_button = button
        break


all_labels = {}
for i in range(7):
    
    day_tab = driver.find_elements_by_xpath('//*[@id=":7"]')
    # day_tab = driver.find_element_by_class_name('goog-inline-block goog-menu-button-caption')
    day_tab = day_tab[0]
    day = int(day_tab.get_attribute('aria-posinset'))
    
    
    # CSS Selector
    s_hour = 3
    e_hour = 27
    labels = []
    for hour in range(s_hour,e_hour):
        css = '.section-popular-times-graph-visible > div:nth-child(' + str(hour) + ')'
        elements = driver.find_elements_by_css_selector(css)
        if len(elements) > 0:
            element = elements[0]
            label = element.get_attribute('aria-label')
            labels.append(label)
        else:
            e_hour = hour
            break
    
    #
    all_labels[day] = labels
    next_button.click()



# Regular expression: extract percentage. See https://docs.python.org/3/library/re.html
import re
re_percentage = re.compile('\d+\%') # re_percentage.search(label).group() gives the percentage. e.g. '40%'
re_hour = re.compile('\d+(?= AM)|\d+(?= PM)|\d+(?=時)') # exclude %, (?!...) excludes, (?=...) is like AND

matches = ['Currently',
           '目前']
# check for words in list matches to see if current time info is available
def get_current(s,matches):
    for match in matches:
        if match in s:
            return(True)

all_pops = {}
s_hour = 24
# e_hour = 0
for key,labels in all_labels.items():
    pops = []
    current = np.nan
    for i,label in enumerate(labels):
        if re_hour.search(label)!= None:
            hour = np.int(re_hour.search(label).group())
            if hour < s_hour:
                s_hour = hour
            # if hour > e_hour-1:
            #     e_hour = hour+1
        # c = label.find('Currently')
        # if c != -1:
        if get_current(label,matches):
            current = i
            print('hour:{}\tpercentage:{}'.format('now',re_percentage.search(label).group()))
        else:
            print('hour:{}\tpercentage:{}'.format(re_hour.search(label).group(),re_percentage.search(label).group()))
        pop = np.int(re_percentage.search(label).group()[:-1])
        pops.append(pop)
        
    all_pops[key] = pops.copy()
    
    
# plot weekly popularity
plt.figure()
for day,pops in all_pops.items():
    plt.plot(np.arange(s_hour,s_hour+len(pops)),pops,label = num2dayofweek[day])
plt.ylim(0,100)
plt.legend()
plt.show()

# bar plot of weekly popularity
plt.figure()
for day,pops in all_pops.items():
    plt.bar(np.arange(s_hour,s_hour+len(pops)),pops,label = num2dayofweek[day],alpha=0.2)
    if ~np.isnan(current):
        plt.bar(np.arange(s_hour,e_hour)[current],pops[current],color='magenta')
    # plt.plot(np.arange(s_hour,e_hour),pops)
plt.ylim(0,100)
plt.legend()
plt.show()

# bar subplots for the week, Method 1
fig,axes = plt.subplots(4,2,sharex='all', sharey='all')
for day,pops in all_pops.items():
    r = (day-1)//2
    c = (day-1)%2
    ax = axes[r,c]
    
    ax.bar(np.arange(s_hour,s_hour+len(pops)),pops,label = '_no_legend_')
    if ~np.isnan(current):
        ax.bar(np.arange(s_hour,s_hour+len(pops))[current],pops[current],color='magenta')
    # ax.plot(np.arange(s_hour,e_hour),pops)
    ax.set_title(num2dayofweek[day])
    ax.set_ylim([0,100])
    # ax.legend()
plt.show()


# bar subplots for the week, Method 2
plt.figure()
for day,pops in all_pops.items():
    # r = (day-1)//2
    # c = (day-1)%2
    # ax = axes[r,c]
    index = 420 + day
    ax = plt.subplot(index)
    ax.bar(np.arange(s_hour,s_hour+len(pops)),pops,label = '_no_legend_')
    if ~np.isnan(current):
        ax.bar(np.arange(s_hour,s_hour+len(pops))[current],pops[current],color='magenta')
    # ax.plot(np.arange(s_hour,e_hour),pops)
    ax.set_title(num2dayofweek[day])
    ax.set_ylim([0,100])
    # ax.legend()
plt.show()

driver.close()
