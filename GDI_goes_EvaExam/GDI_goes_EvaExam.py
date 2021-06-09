import mammoth.documents
import mammoth.transforms
import re

fileobj="Test.docx"

html_string = mammoth.convert_to_html(
    fileobj,
    style_map=  """
                   b => b
                   i => i
    """
).value

############ Check for common user mistakes
lists = re.compile('(</?ul>)|(</?li>)')
if lists.search(html_string):
    print("Found list items or list templates (Formatvorlagen)! Clear your input, please!")
    exit()

############# HTML-String RegEx
# Handle paragraphs
paragraphs = re.compile('<p>(.*?)</p>')
html_string = paragraphs.sub(r'\1</br>', html_string)
# Remove everything until first group
html_string = re.compile(r'.*?(Group: .+?</br>)').sub(r'\1', html_string, 1)
# Find groups
groups = re.compile(r'(Group: .+?)</br>')
html_string = groups.sub(r'\n\n\n\1', html_string)
# Find Questiontags
html_string = re.compile(r'((<[\w/]*>)|\s+)*SC(<[\w/]*>)*\s*</br>').sub(r'\n\nSC\n', html_string)
# Find Questions
tasks = re.compile(r'\n\nSC\n').split(html_string)
html_string = ""
for task in tasks:
    # Find answers
    answer = re.compile(r'(?:<[\w/]*?>)*(\d\t)')
    if answer.findall(task):
        # Seperate answers with new line
        task = answer.sub(r'\n\1', task)
        # Split question and answers to substitute tabs with html
        question_and_answer = answer.split(task, 1)
        task = question_and_answer[0].replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;') + question_and_answer[1] + question_and_answer[2]
    html_string += task + '\n\nSC\n'
# Remove unnecessary SC at the end
html_string = rreplace(html_string, '\n\nSC\n', '', 1)

############# Write document
with open('output.txt', 'w') as html_file:
        html_file.write(html_string)