import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time

# This script modifies an EvaExam grades export with data from lehreadm.ihr.uni-stuttgart.de to assign bonus points to students who passed the online exam
# Grades are also updated using either a dynamic (self-generated) grades list or a static grades list

valid_grades = [1.0,1.3,1.7,2.0,2.3,2.7,3.0,3.3,3.7,4.0,5.0]

# Manually set static grades list, just uncomment and adapt grades (optionaler statischer Notenschlüssel - es werden dann keine Noten abgefragt!)
#static_points_to_grades = [(4.0,10),(3.7,15),(3.3,20),(3.0,25),(2.7,30),(2.3,37),(2.0,40),(1.7,48),(1.3,50),(1.0,55)]

def wait_for(condition_function):
    start_time = time.time()
    while time.time() < start_time + 3:
        if condition_function():
            return True
        else:
            time.sleep(0.1)
    raise Exception(
        'Timeout waiting for {}'.format(condition_function.__name__)
    )

class wait_for_page_load(object):
    # Selenium driver should wait for the website to load, necessary because of java script, ajax, etc.
    # Class can be used as context manager
    def __init__(self, browser):
        self.browser = browser
    def __enter__(self):
        self.old_page = self.browser.find_element_by_tag_name('html')
    def page_has_loaded(self):
        new_page = self.browser.find_element_by_tag_name('html')
        return new_page.id != self.old_page.id
    def __exit__(self, *_):
        wait_for(self.page_has_loaded)

def determine_static_mark(student_points, points_to_grades):
    current_mark = 4.0
    for mark, min_points in points_to_grades:
        if (student_points >= min_points):
            current_mark = mark
    return current_mark

def determine_mark(student_points, points_to_grades_dict):
    # Determine mark using static grades list (if defined)
    if ('static_points_to_grades' in globals()):
        print("Using static grades list. To change to dynamic grades list, comment static_points_to_grades variable.")
        return determine_static_mark(student_points, static_points_to_grades)
    # Determine mark using (incomplete) grades list
    print("Using dynamic grades list. To change to static grades list, uncomment static_points_to_grades variable and assign a points->grades list.")
    if (student_points in points_to_grades_dict):
        return points_to_grades_dict[student_points]
    # If grades do not include current student_points value, enter correct grade and complement grades list
    else:
        mark = None
        while not mark:
            mark = float(input(f"Enter mark for {student_points} points as X.X: "))
            if mark in valid_grades:
                points_to_grades_dict[student_points] = mark
                return mark
        
if __name__ == "__main__":
    points_to_give = int(input("How many points should the successful students receive? "))
    user = input("Enter username for lehreadm: ")
    password = input("Enter password for lehreadm: ")
    # Get Mat.-Nr. of students who passed their online exam
    driver = webdriver.Chrome(executable_path=ChromeDriverManager().install())
    successful_student_site = f'https://{user}:{password}@lehreadm.ihr.uni-stuttgart.de/#!u-statistic/'
    with wait_for_page_load(driver):
        driver.get(successful_student_site)
    html = driver.page_source
    html = driver.execute_script("return document.documentElement.innerHTML")
    soup = BeautifulSoup(html, 'lxml')
    successful_student_classes = soup.find_all('a', class_="GOBJYLXBHR-de-stuttgart-uni-ihr-webselftestpro-admin-client-util-UserWidget_BinderImpl_GenCss_style-title")
    successful_student_numbers = []
    for successful_student in successful_student_classes:
        successful_student_numbers.append(int(successful_student.text[0:7]))
    print (f"Imported {len(successful_student_numbers)} students!")
    driver.close()
    # Import EvaExam export file, change points and grades accordingly for students who passed their online exam
    students = pd.read_csv("gradestest.csv", encoding='latin1', delimiter=';', decimal=',')
    points_to_grades_dict = {}
    # Determine grades list (Notenschlüssel)
    for student in students.to_dict('records'):
        points_to_grades_dict[student['Summe Punkte']] = student['Note']
    students['Summe Punkte'] = students[['Prüfungsteilnehmer-ID','Summe Punkte']].apply(lambda x: x['Summe Punkte'] + points_to_give if x['Prüfungsteilnehmer-ID'] in successful_student_numbers else x['Summe Punkte'], axis=1)
    students['Note'] = students[['Prüfungsteilnehmer-ID', 'Summe Punkte', 'Note']].apply(lambda x: determine_mark(x['Summe Punkte'], points_to_grades_dict) if x['Prüfungsteilnehmer-ID'] in successful_student_numbers else x['Note'], axis=1).astype(float)
    students.to_csv("gradesresults.csv", index=False, encoding='latin1', sep=';', decimal=',')