import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time
import sys


print("This script generates an updated EvaExam grades export (updated_grades.csv) from an original export (grades.csv) which must be places inside the script root directory.")
print("It uses data from lehreadm.ihr.uni-stuttgart.de to assign bonus points to students who passed the online exam.")
print("Their grades are then updated using either a self-generated grades list from the other students' data where missing data points must be inputted interactively by the user or using a static grades list (static_points_to_grades) which can be defined inside the script itself.")

valid_grades = [1.0,1.3,1.7,2.0,2.3,2.7,3.0,3.3,3.7,4.0,5.0]

# Manually set static grades list, just uncomment and adapt grades (optionaler statischer Notenschlüssel - es werden dann keine Noten interaktiv abgefragt!)
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
    if not hasattr(determine_mark, 'printed_info'):
        determine_mark.printed_info = False
        # Determine mark using static grades list (if defined)
    if ('static_points_to_grades' in globals()):
        if not determine_mark.printed_info:
            print("Using static grades list. To change to dynamic grades list, comment static_points_to_grades variable.")
            determine_mark.printed_info = True
        return determine_static_mark(student_points, static_points_to_grades)
    # Determine mark using (incomplete) grades list
    if not determine_mark.printed_info:
        print("Using dynamic grades list. To change to static grades list, uncomment static_points_to_grades variable and assign a points->grades list.")
        determine_mark.printed_info = True
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

def correct_url_encoding(string):
    encoding_dict = {' ':'%20', '!':'%21','"':'%22','#':'%23','$':'%24','%':'%25','&':'%26',"'":'%27','(':'%28',')':'%29','*':'%2A','+':'%2B',',':'%2C','-':'%2D','.':'%2E','/':'%2F',':':'%3A',';':'%3B','<':'%3C','=':'%3D','>':'%3E','?':'%3F','@':'%40','[':'%5B','\\':'%5C',']':'%5D','{':'%7B','|':'%7C','}':'%7D'}
    for key, val in encoding_dict.items():
        string = string.replace(key, val)
    return string
        
if __name__ == "__main__":
    import_successful_student_numbers = None
    while (import_successful_student_numbers != 'Y' and import_successful_student_numbers != 'N'):
        import_successful_student_numbers = (input("Do you want to import an existing successful student file (successful_student_numbers.csv) from a previous run of this script? Choosing 'N' will load the data from lehreadm-Portal instead. [Y/N] "))
    # Get successful student data from Lehreportal
    successful_student_numbers = []
    if (import_successful_student_numbers == 'N'):
        user = input("Enter username for lehreadm: ")
        password = input("Enter password for lehreadm: ")
        user = correct_url_encoding(user)
        password = correct_url_encoding(password)
        # Get Mat.-Nr. of students who passed their online exam
        driver = webdriver.Chrome(executable_path=ChromeDriverManager().install())
        successful_student_site = f'https://{user}:{password}@lehreadm.ihr.uni-stuttgart.de/#!u-statistic/'
        with wait_for_page_load(driver):
            driver.get(successful_student_site)
        html = driver.page_source
        html = driver.execute_script("return document.documentElement.innerHTML")
        soup = BeautifulSoup(html, 'lxml')
        successful_student_classes = soup.find_all('a', class_="GOBJYLXBHR-de-stuttgart-uni-ihr-webselftestpro-admin-client-util-UserWidget_BinderImpl_GenCss_style-title")
        for successful_student in successful_student_classes:
            successful_student_numbers.append(int(successful_student.text[0:7]))
        print (f"Imported {len(successful_student_numbers)} students!")
        driver.close()
        export_successful_student_numbers = (input("Do you want to export as successful_student_numbers.csv? Choosing 'N' will instead directly write the data from lehreadm-Portal to your EvaExam file [Y/N]"))
        if (export_successful_student_numbers == 'Y'):
            with open('successful_student_numbers.csv', 'w', newline='\n') as file:
                 wr = csv.writer(file)
                 wr.writerow(successful_student_numbers)
            sys.exit("Export File successful_student_numbers.csv was written! Exiting...")
    # Import student numbers from file
    else:
        with open('successful_student_numbers.csv', newline='\n') as file:
            reader = csv.reader(file)
            successful_student_numbers = [int(f) for f in (list(reader)[0])]
    # Import EvaExam export file, change points and grades accordingly for students who passed their online exam
    students = pd.read_csv("grades.csv", encoding='latin1', delimiter=';', decimal=',')
    points_to_grades_dict = {}
    # Determine grades list (Notenschlüssel)
    for student in students.to_dict('records'):
        points_to_grades_dict[student['Summe Punkte']] = student['Note']
    # Alter grades in EvaExam File
    points_to_give = int(input("How many points should the successful students receive? "))
    students['Summe Punkte'] = students[['Prüfungsteilnehmer-ID','Summe Punkte']].apply(lambda x: x['Summe Punkte'] + points_to_give if x['Prüfungsteilnehmer-ID'] in successful_student_numbers else x['Summe Punkte'], axis=1)
    students['Note'] = students[['Prüfungsteilnehmer-ID', 'Summe Punkte', 'Note']].apply(lambda x: determine_mark(x['Summe Punkte'], points_to_grades_dict) if x['Prüfungsteilnehmer-ID'] in successful_student_numbers else x['Note'], axis=1).astype(float)
    students.to_csv("updated_grades.csv", index=False, encoding='latin1', sep=';', decimal=',')