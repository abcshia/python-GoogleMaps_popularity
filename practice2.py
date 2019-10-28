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

import time

# Set webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

'''
Finding parent element using XPATH:
    find_element_by_xpath('..')
    
Finding child element using XPATH:
    find_elements_by_xpath(".//*")

Finding child element using CSS:
    find_elements_by_css_selector("*")
    
--------------------------------------
parent of the parent : By.xpath("../..")
    
'..' means parent
'./' means element itself
'*' means anything/everything
'''

## General set up
dayofweek = [['Monday','星期一'],
             ['Tuesday','星期二'],
             ['Wednesday','星期三'],
             ['Thursday','星期四'],
             ['Friday','星期五'],
             ['Saturday','星期六'],
             ['Sunday','星期日']
             ]
             
dayofweek_eng = ['Monday',
                'Tuesday',
                'Wednesday',
                'Thursday',
                'Friday',
                'Saturday',
                'Sunday'
                ]
                
num2dayofweek = {1:'Monday',
                 2:'Tuesday',
                 3:'Wednesday',
                 4:'Thursday',
                 5:'Friday',
                 6:'Saturday',
                 7:'Sunday'
                }
day2num = {}
for k,v in num2dayofweek.items():
    day2num[v] = k


month2num = {'January' : 1,
             'February' : 2,
             'March' : 3,
             'April' : 4,
             'May' : 5,
             'June' : 6,
             'July' : 7,
             'August' : 8,
             'September' : 9,
             'October' : 10,
             'November' : 11,
             'December' : 12
             }


## Popularity/Opening hours data scraping

# Chrome
from selenium.webdriver.chrome.options import Options
driverPath = r'C:\Users\James\OneDrive\PythonFiles\packages\selenium\WebDrivers\chromedriver.exe'
chrome_options = Options()
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--incognito")
# chrome_options.add_argument("--window-size=1920x1080")
driver = webdriver.Chrome(chrome_options=chrome_options, executable_path = driverPath)

# Firefox
driverPath = r'C:\Users\James\OneDrive\PythonFiles\packages\selenium\WebDrivers\geckodriver.exe'
from selenium.webdriver.firefox.options import Options
options = Options()
# options.add_argument("--headless")
options.add_argument("--private")
driver = webdriver.Firefox(firefox_options=options, executable_path = driverPath)




# search key words
search_words = 'Hong Kong East Ocean Seafood Restaurant, emeryville'#'Hong Kong East Ocean Seafood Restaurant' #'Recreational Sports Facility'#'noodles fresh'#'Monterey Market'#'Grégoire Restaurant' #'daimo'#'Asian Pearl Seafood Restaurant'

# get search results from google maps
html_url = 'https://maps.google.com'
driver.get(html_url)
WebDriverWait(driver,60).until(EC.presence_of_element_located((By.ID, 'searchboxinput')))

searchbox = driver.find_element_by_id('searchboxinput')
searchbox.send_keys(search_words)
# searchbox.submit()
searchbutton = driver.find_element_by_id('searchbox-searchbutton')
searchbutton.click()


## == Popularity data ==
# wait to load page
WebDriverWait(driver,60).until(EC.presence_of_element_located((By.CLASS_NAME, 'section-popular-times')))



# Get weekly data:
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
all_pops_day = {}
s_hour = 24 # starting hour for popular data
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
    all_pops_day[num2dayofweek[key]] = pops.copy()

print(pd.DataFrame(all_pops_day).T)

    
# plot weekly popularity
plt.figure()
for day,pops in all_pops.items():
    plt.plot(np.arange(s_hour,s_hour+len(pops)),pops,label = num2dayofweek[day])
plt.ylim(0,100)
plt.legend()
plt.show()

# # bar plot of weekly popularity
# plt.figure()
# for day,pops in all_pops.items():
#     plt.bar(np.arange(s_hour,s_hour+len(pops)),pops,label = num2dayofweek[day],alpha=0.2)
#     if ~np.isnan(current):
#         plt.bar(np.arange(s_hour,e_hour)[current],pops[current],color='magenta')
#     # plt.plot(np.arange(s_hour,e_hour),pops)
# plt.ylim(0,100)
# plt.legend()
# plt.show()
# 
# # bar subplots for the week, Method 1
# fig,axes = plt.subplots(4,2,sharex='all', sharey='all')
# for day,pops in all_pops.items():
#     r = (day-1)//2
#     c = (day-1)%2
#     ax = axes[r,c]
#     
#     ax.bar(np.arange(s_hour,s_hour+len(pops)),pops,label = '_no_legend_')
#     if ~np.isnan(current):
#         ax.bar(np.arange(s_hour,s_hour+len(pops))[current],pops[current],color='magenta')
#     # ax.plot(np.arange(s_hour,e_hour),pops)
#     ax.set_title(num2dayofweek[day])
#     ax.set_ylim([0,100])
#     # ax.legend()
# plt.show()


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






## == Opening hours data ==
classname = 'section-info-hour-text'
obj = driver.find_elements_by_class_name(classname)
obj = obj[0]
# in case the element is covered by another element, making it not clickable
# driver.execute_script("arguments[0].click();", obj)
obj.click()

classname = 'widget-pane-info-open-hours-row-table-hoverable'
obj = driver.find_elements_by_class_name(classname)
obj = obj[0]
openhour_text = obj.text

print(openhour_text)


# == Formatting time using regular expression ==
# re_time = re.compile('\d{1,2}[:]\d{2}((AM)|(PM)|())–\d{1,2}[:]\d{2}((AM)|(PM)|())')
# re_time = re.compile('\d{1,2}:\d{2}((AM)|(PM)|())–\d{1,2}:\d{2}((AM)|(PM)|())')
re_time = re.compile('\d{1,2}(((AM)|(PM)|())|(:\d{2}((AM)|(PM)|())))–\d{1,2}(((AM)|(PM))|(:\d{2}((AM)|(PM)|())))')


# hours = []
# hour = re_time.search(openhour_text)
# while hour != None:
#     hours.append(openhour_text[hour.start():hour.end()])
#     hour = re_time.search(openhour_text,hour.end())


# openhours = dict(zip(dayofweek_eng,hours))


# get starting positions of days
pos = 0
s_positions = []
for day in dayofweek:
    for format in day:
        pos = openhour_text.find(format,pos)
        if pos != -1:
            s_positions.append(pos)
        else:
            pos = 0

# get open hours
weekly_hours = {}
for i,pos in enumerate(s_positions):
    try:
        j = (i+1)%len(s_positions)
        e_pos = s_positions[j]
        if e_pos == 0: e_pos = len(openhour_text)
    except:
        e_pos = len(openhour_text)
    
    hours = []
    hour = re_time.search(openhour_text,pos,e_pos)
    
    while hour != None and hour.end() <= e_pos:
        hours.append(openhour_text[hour.start():hour.end()])
        hour = re_time.search(openhour_text,hour.end(),e_pos)
    
    # weekly_hours[i] = hours
    weekly_hours[dayofweek_eng[i]] = hours
    
print(pd.DataFrame(weekly_hours).T)


## == Travel time data ==

def parse_YM_eng_chi(date): # only for English or Chinese
    '''
    input:
        date - string
    output:
        [month,year] - month and year are strings
    '''
    eng = date.find('月') == -1
    
    if eng:
        month,year = date.split()
        month = month2num[month]
    else:
        year,month = date.split('年')
        month = month.split('月')[0]
        
    return([month,year,eng])


origin = 'Great mall, Milpitas'
departure_time = '15:20'
# departure_date = 'June 5, 2019'
departure_day = '8'
departure_month = '3'
departure_year = '2019'


# == Our Strategy here to avoid strange errors from the driver and retry == !!!
# while True:
#         try:
#             # do stuff
#         except SomeSpecificException:
#             continue
#         break


while True:
    try:
        # Find 'direction' button
        match_words = ['Directions','規劃路線']
        match = False
        
        WebDriverWait(driver,60).until(EC.presence_of_element_located((By.TAG_NAME, 'button')))
        # WebDriverWait(driver,60).until(EC.visibility_of_element_located((By.TAG_NAME, 'button')))
        buttons = driver.find_elements_by_tag_name('button')
        for button in buttons:
            for word in match_words:
                if button.get_attribute('data-value') == word:
                    direction_button = button
                    break
                    
            if match: break
        time.sleep(1)
        direction_button.click()
        
        WebDriverWait(driver,60).until(EC.presence_of_element_located((By.CLASS_NAME,'tactile-searchbox-input')))
        # Send in search words for origin and press enter without specifying element
        actions = ActionChains(driver)
        actions.send_keys(origin)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        
        WebDriverWait(driver,60).until(EC.visibility_of_element_located((By.CLASS_NAME, 'goog-menu-button-dropdown')))
        # Find 'Leave now' ('立即出發') button and click
        button = driver.find_elements_by_class_name('goog-menu-button-dropdown')[-1] # goog-inline-block goog-menu-button kd-button kd-button-transparent
        time.sleep(1)
        button.click()
        
        WebDriverWait(driver,60).until(EC.presence_of_element_located((By.CLASS_NAME, 'goog-menuitem-content')))
        # options = driver.find_elements_by_class_name('goog-menuitem-content') # goog-menuitem-content
        options = driver.find_elements_by_class_name('goog-menu-vertical')
        
        # leave_now = options[0]
        # depart_at = options[1]
        # arrive_by = options[2]
        
        word_list = ['Depart at','出發時間']
        depart_at = None
        for option in options:
            print(option.text+'\n+')
            
            for word in word_list:
                if option.text.find(word) > 0:
                    print(option.text)
                    depart_at = option
                    break
            if depart_at: break
        
        time.sleep(1)
        depart_at.click()
        # WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID,depart_at.id))).click()
        # driver.execute_script("arguments[0].click();", depart_at)
        
        
        # Set departure time
        WebDriverWait(driver,60).until(EC.presence_of_element_located((By.NAME,'transit-time')))
        timebox = driver.find_element_by_name('transit-time')
        timebox.send_keys(Keys.CONTROL,'a') # Ctrl+A
        timebox.send_keys(Keys.DELETE)
        timebox.send_keys(departure_time)
        
        # Set departure date:
        WebDriverWait(driver,60).until(EC.presence_of_element_located((By.CLASS_NAME,'date-input')))
        datebox = driver.find_element_by_class_name('date-input')
        datebox.click()
        WebDriverWait(driver,60).until(EC.presence_of_element_located((By.CLASS_NAME,'goog-date-picker-monthyear')))
        date_picker = driver.find_elements_by_class_name('goog-date-picker-monthyear')[-1]
        print(date_picker.text)
        
        
        # Set month
        
        pre_button = driver.find_elements_by_class_name('goog-date-picker-previousMonth')[-1]# goog-date-picker-btn goog-date-picker-previousMonth
        next_button = driver.find_elements_by_class_name('goog-date-picker-nextMonth')[-1]# goog-date-picker-btn goog-date-picker-nextMonth
        
        # calculate month difference
        month,year,eng = parse_YM_eng_chi(date_picker.text)
        dm = int(departure_month) - int(month)
        dy = int(departure_year) - int(year)
        d = dy * 12 + dm # difference
        
        if d > 0:
            button = next_button
        elif d < 0:
            button = pre_button
            d = -d
        
        for i in range(d):
            button.click()
            time.sleep(1)  
        
        
        
        # Set day of month
        days = driver.find_elements_by_tag_name('td')
        
        for day in days:
            if day.get_attribute('role') == 'gridcell' and day.text == departure_day:
                break
        
        day.click()
        
        
        WebDriverWait(driver,60).until(EC.presence_of_element_located((By.CLASS_NAME, 'section-directions-trip-duration')))
        # Get travel time data
        ele = driver.find_element_by_class_name('section-directions-trip-duration') # section-directions-trip-duration
        travel_text = ele.text
    except:
        continue
    break






# typically 1 h 5 min - 2 h 10 min
# 預估行車時間：1 小時 5 分 - 2 小時 10 分

import re
# # re_eng = re.compile('\d+ (h) \d+ (min) - \d+ (h) \d+ (min)')
# # re_chi = re.compile('\d+ (小時) \d+ (分) - \d+ (小時) \d+ (分)')
# re_time = re.compile('\d* (h|小時)* \d* (min|分)* - \d* (h|小時)* \d* (min|分)*')
# # re_time.search(travel_text)
# 
# # re_h_m = re.compile('\d+ (h|小時) \d+ (min|分)')
# 
# try:
#     s = re_time.search(travel_text).start()
#     e = re_time.search(travel_text).end()
#     duration_text = travel_text[s:e]
#     print(duration_text)
#     
#     dura1, dura2 = duration_text.split('-')
#     if eng:
#         h1 = int(dura1.split('h')[0])
#         m1 = int(dura1.split('h')[1].split('min')[0])
#         h2 = int(dura2.split('h')[0])
#         m2 = int(dura2.split('h')[1].split('min')[0])
#     else:
#         h1 = int(dura1.split('小時')[0])
#         m1 = int(dura1.split('小時')[1].split('分')[0])
#         h2 = int(dura2.split('小時')[0])
#         m2 = int(dura2.split('小時')[1].split('分')[0])
#     
#     print('Duration:\n{}h {}min\n{}h {}min'.format(h1,m1,h2,m2))
# 
# except:
#     import sys
#     print(print(sys.exc_info()[0]))



texts = travel_text.split('-')
texts.reverse() # search backwards in case there are no units

dura_list = []

re_h = re.compile('\d* (h|小時)')
re_m = re.compile('\d* (min|分)')
for i,text in enumerate(texts):
    hs = re_h.search(text).start() if re_h.search(text)!=None else None
    ms = re_m.search(text).start() if re_m.search(text)!=None else None
    he = re_h.search(text).end() if re_h.search(text)!=None else None
    me = re_m.search(text).end() if re_m.search(text)!=None else None
    
    # No units
    if hs==None and ms==None:
        re_digits = re.compile('\d{1,2}')
        ms = re_digits.search(text).start() if re_digits.search(text)!=None else None
        me = re_digits.search(text).end() if re_digits.search(text)!=None else None
    
    
    h = int(text[hs:he].split()[0]) if hs != None else 0
    m = int(text[ms:me].split()[0]) if ms != None else 0
    
    dura_list.append('{}h{}m'.format(h,m))
    

dura_list.reverse() # reverse back    
print(dura_list)












# # Find origin search bar
# searchbox = driver.find_element_by_class_name('tactile-searchbox-input')
# searchbox.send_keys(origin) # This doesn't work
# 
# button = driver.find_element_by_class_name('searchbox-searchbutton')
# driver.execute_script("arguments[0].click();", button) # button.click()





# # == Notes ==
# # For <select> elements
# from selenium.webdriver.support.ui import Select 
# 
# # find active element
# searchbox = driver.switch_to_active_element 
# 
# # hover mouse
# from selenium.webdriver.common.action_chains import ActionChains
# hover = ActionChains(driver).move_to_element(searchbox)
# hover.perform()
# 
# driver.execute_script("arguments[0].setAttribute('class', 'searchbox  sbox-hover');", hover_elem)
# 
# # Send keys without specifying element
# from selenium.webdriver.common.action_chains import ActionChains
# actions = ActionChains(self.driver)
# actions.send_keys('dummydata')
# actions.perform()
# 
# 
# # wait until clickable
# WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "h3.title-and-badge.style-scope.ytd-video-renderer a"))).click()
# #
# driver.execute_script("arguments[0].scrollIntoView(true);", page)
# 
# # Execute using JavaScript in case something is blocking the element
# driver.execute_script("arguments[0].click();", searchbox)
# driver.execute_script("arguments[0].setAttribute('value', 'Great mall, milpitas');", searchbox)
# 







## Close driver


driver.close()
driver.quit()

## Functions

def find_count(s,sub):
    count = 0
    pos = 0
    
    while s.find(sub,pos) != -1:
        count += 1
        pos = s.find(sub,pos) + len(sub)
    
    return(count)

def time2format(time_string):
    # am = True if time_string.find('AM') != -1 else False
    # pm = True if time_string.find('PM') != -1 else False
    am = find_count(time_string,'AM')
    pm = find_count(time_string,'PM')
    
    if am+pm == 0: # 24 hour clock
        time_format = 24 #'%H:%M'
    else: # 12 hour clock
        time_format = 12 #'%I:%M'
    
    hour_only = True if time_string.find(':')==-1 else False
    
    # remove AM PM
    time_string = time_string.replace('AM','')
    time_string = time_string.replace('PM','')
    
    if time_format == 12:
        if hour_only:
            H = int(time_string)
            if pm > 0: H+=12
            H = '{:02}'.format(H)
            M = '00'
        else:
            H,M = time_string.split(':')
            H = int(H)
            if pm > 0: H+=12
            H = '{:02}'.format(H)
            
    elif time_format == 24:
        if hour_only:
            H = int(time_string)
            M = '00'
        else:
            H,M = time_string.split(':')
            H = int(H)
            H = '{:02}'.format(H)
        
    return(H+M)


def scrape_gmaps(search_words,driver,plots = False):
    # General set up
    dayofweek = [['Monday','星期一'],
                ['Tuesday','星期二'],
                ['Wednesday','星期三'],
                ['Thursday','星期四'],
                ['Friday','星期五'],
                ['Saturday','星期六'],
                ['Sunday','星期日']
                ]
                
    dayofweek_eng = ['Monday',
                    'Tuesday',
                    'Wednesday',
                    'Thursday',
                    'Friday',
                    'Saturday',
                    'Sunday'
                    ]
                    
    num2dayofweek = {1:'Monday',
                    2:'Tuesday',
                    3:'Wednesday',
                    4:'Thursday',
                    5:'Friday',
                    6:'Saturday',
                    7:'Sunday'
                    }
    day2num = {}
    for k,v in num2dayofweek.items():
        day2num[v] = k
    
    # # Chrome
    # from selenium.webdriver.chrome.options import Options
    # driverPath = r'C:\Users\James\OneDrive\PythonFiles\packages\selenium\WebDrivers\chromedriver.exe'
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--incognito")
    # # chrome_options.add_argument("--window-size=1920x1080")
    # driver = webdriver.Chrome(chrome_options=chrome_options, executable_path = driverPath)
    
    # get search results from google maps
    html_url = 'https://maps.google.com'
    driver.get(html_url)
    WebDriverWait(driver,60).until(EC.presence_of_element_located((By.ID, 'searchboxinput')))
    
    searchbox = driver.find_element_by_id('searchboxinput')
    searchbox.send_keys(search_words)
    # searchbox.submit()
    searchbutton = driver.find_element_by_id('searchbox-searchbutton')
    searchbutton.click()
    
    # == POPULARITY DATA ==
    # wait to load page
    WebDriverWait(driver,60).until(EC.presence_of_element_located((By.CLASS_NAME, 'section-popular-times')))
    
    # Get weekly data:
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
    all_pops_day = {}
    s_hour = 24 # starting hour for popular data
    # e_hour = 0
    for key,labels in all_labels.items():
        pops = []
        current = np.nan
        for i,label in enumerate(labels):
            if re_hour.search(label)!= None:
                hour = np.int(re_hour.search(label).group())
                if hour < s_hour:
                    s_hour = hour
            if get_current(label,matches):
                current = i
                print('hour:{}\tpercentage:{}'.format('now',re_percentage.search(label).group()))
            else:
                print('hour:{}\tpercentage:{}'.format(re_hour.search(label).group(),re_percentage.search(label).group()))
            pop = np.int(re_percentage.search(label).group()[:-1])
            pops.append(pop)
            
        all_pops[key] = pops.copy()
        all_pops_day[num2dayofweek[key]] = pops.copy()
    
    print(pd.DataFrame(all_pops_day).T)
    
    if plots:
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
        
        # bar subplots for the week
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
    
    # == OPEN HOURS ==
    classname = 'section-info-hour-text'
    obj = driver.find_elements_by_class_name(classname)
    obj = obj[0]
    # in case the element is covered by another element, making it not clickable
    # driver.execute_script("arguments[0].click();", obj)
    obj.click()
    
    classname = 'widget-pane-info-open-hours-row-table-hoverable'
    obj = driver.find_elements_by_class_name(classname)
    obj = obj[0]
    openhour_text = obj.text
    
    print(openhour_text)
    
    
    # == Formatting time using regular expression ==
    re_time = re.compile('\d{1,2}(((AM)|(PM)|())|(:\d{2}((AM)|(PM)|())))–\d{1,2}(((AM)|(PM))|(:\d{2}((AM)|(PM)|())))')
    
    # get starting positions of days
    pos = 0
    s_positions = []
    for day in dayofweek:
        for format in day:
            pos = openhour_text.find(format,pos)
            if pos != -1:
                s_positions.append(pos)
            else:
                pos = 0
    
    # get open hours
    weekly_hours = {}
    for i,pos in enumerate(s_positions):
        try:
            j = (i+1)%len(s_positions)
            e_pos = s_positions[j]
            if e_pos == 0: e_pos = len(openhour_text)
        except:
            e_pos = len(openhour_text)
        
        hours = []
        hour = re_time.search(openhour_text,pos,e_pos)
        
        while hour != None and hour.end() <= e_pos:
            hours.append(openhour_text[hour.start():hour.end()])
            hour = re_time.search(openhour_text,hour.end(),e_pos)
        
        # weekly_hours[i] = hours
        weekly_hours[dayofweek_eng[i]] = hours
        
    print(pd.DataFrame(weekly_hours).T)
    
    
    # driver.close()
    return(all_pops,all_pops_day,s_hour,weekly_hours)



def format_open_hours(weekly_hours):
    open_hours = {}
    for day,periods in weekly_hours.items():
        open_hours[day] = []
        
        for p in periods:
            s,e = p.split('–')
            
            am = find_count(p,'AM')
            pm = find_count(p,'PM')
            apm = ''
            if am+pm == 1:
                if am == 1:
                    apm = 'AM'
                elif pm == 1:
                    apm = 'PM'
            s = s + apm
            e = e + apm
            
            s = time2format(s)
            e = time2format(e)
            open_hours[day].append([s,e])
    print(open_hours)
    return(open_hours)


## Formating time


open_hours = {}
for day,periods in weekly_hours.items():
    open_hours[day] = []
    
    for p in periods:
        s,e = p.split('–')
        
        am = find_count(p,'AM')
        pm = find_count(p,'PM')
        apm = ''
        if am+pm == 1:
            if am == 1:
                apm = 'AM'
            elif pm == 1:
                apm = 'PM'
        s = s + apm
        e = e + apm
        
        s = time2format(s)
        e = time2format(e)
        open_hours[day].append([s,e])
    
    
    
    
## Places: Location data

# Load google api key
with open('api-key.txt','r') as f:
    apikey = f.read()

search_words = 'Hong Kong East Ocean Seafood Restaurant'#'Recreational Sports Facility'

gmaps = googlemaps.Client(key=apikey)
places = gmaps.places(search_words)

# places['status'] == 'OK'
# places['status'] == 'ZERO_RESULTS'

if places['status'] == 'OK':
    address = places['results'][0]['formatted_address']
    gps_location = places['results'][0]['geometry']['location']
    place_id = places['results'][0]['place_id']
    name = places['results'][0]['name']
    opening_hours = places['results'][0]['opening_hours']
    types = places['results'][0]['types']
    rating = places['results'][0]['rating']
    total_ratings = places['results'][0]['user_ratings_total']

# Lacking popular data and opening hours data! Scrape with Selenium or use 'place' in API with place_id 

# place = gmaps.place(place_id)


# Set up driver
from selenium.webdriver.chrome.options import Options
driverPath = r'C:\Users\James\OneDrive\PythonFiles\packages\selenium\WebDrivers\chromedriver.exe'
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--incognito")
# chrome_options.add_argument("--window-size=1920x1080")
driver = webdriver.Chrome(chrome_options=chrome_options, executable_path = driverPath)

# Get popularity and open hour data
all_pops,all_pops_day,s_hour,weekly_hours = scrape_gmaps(search_words,driver,plots = True)
driver.close()
# Format the open hours data
open_hours = format_open_hours(weekly_hours)




# Set up dataset
# locations = {} # key = place_id, val = location dict

location = {'name' : name,
            'address' : address,
            'gps' : gps_location,
            'id' : place_id,
            'types' : types,
            'rating' : rating,
            'total_ratings' : total_ratings,
            'pop' : [all_pops_day,s_hour], # location is the starting hour for popular data
            'open' : open_hours # format: HHMM (24 hour clock) e.g. 3:30PM is 1530
            }

# locations[place_id] = location

# Save data using h5py and json format
try:
    import h5py,json,sys
    f = h5py.File('Test.hdf5','w')
    f.create_dataset(json.dumps(gps_location),data = json.dumps(location))
    f.flush() # to make sure data writes to disk
    print('Location data saved!')
except:
    print(sys.exc_info()[0])
finally:
    f.close()

# Load data
with h5py.File('Test.hdf5','r') as f:
    import sys
    try:
        location = json.loads(f[json.dumps(gps_location)].value)
        print('Location data loaded')
    except AttributeError:
        print('Unable to open object')
    except:
        print(sys.exc_info()[0])

## Distance data
# Load google api key
with open('api-key.txt','r') as f:
    apikey = f.read()

origin = location['gps']#'37.8374895,-122.314807'
destination = {'lat':37.855106, 'lng':-122.211651} # '37.855106, -122.211651'


# Distance matrix querry:
# mode: “driving”, “walking”, “transit” or “bicycling”
# avoid: “tolls”, “highways” or “ferries”
# units: “metric” or “imperial”
# departure_time (int or datetime.datetime)
# arrival_time (int or datetime.datetime)

from datetime import datetime
now = datetime.now()
d_time = datetime.strptime(now.strftime('%Y%m%d')+'1632','%Y%m%d%H%M')
d_time = datetime.strptime('201905301632','%Y%m%d%H%M')

gmaps = googlemaps.Client(key=apikey)
dmatrix = gmaps.distance_matrix(origin, destination, mode='driving',departure_time=d_time) # departure_time, arrival_time

dist = dmatrix['rows'][0]['elements'][0]
# dist_data[origin][destination] = dictionary with 'disance' and 'duration' as keys
dist_data = {origin:{destination:dist}}
















































