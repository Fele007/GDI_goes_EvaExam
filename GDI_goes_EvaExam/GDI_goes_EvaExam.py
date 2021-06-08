import mammoth.documents
import mammoth.transforms
import re

fileobj="Test.docx"

def transform_run(run):
    return run#.copy(style_id="code", style_name="Code")

def rreplace(s, old, new, occurrence):
 li = s.rsplit(old, occurrence)
 return new.join(li)

html_string = mammoth.convert_to_html(
    fileobj,
    transform_document=mammoth.transforms.paragraph(transform_run),
    style_map=  """
                   b => b                
    """
).value

############# HTML-String RegEx ###############
lists = re.compile('(</?ul>)|(</?li>)')
if lists.search(html_string):
    print("Found list items or list templates (Formatvorlagen)! Clear your input, please!")
    exit()
paragraphs = re.compile('<p>')
html_string = paragraphs.sub('', html_string)
breaks = re.compile('</p>')
html_string = breaks.sub('</br>', html_string)
# Remove everything until first group
groups = re.compile('.*?(Group: .*?)</br>')
html_string = groups.sub(r'\1\n\n', html_string,1)
# Find groups
groups = re.compile('(Group: .*?)</br>')
html_string = groups.sub(r'\n\n\1\n\n', html_string)
# Find Questions
questions = re.compile(r'SC.*?</br>').split(html_string)
new_html_string = questions[0]
for question in questions[1:]:
    #question = questions.sub(r'\n\nSC\n', question)
    question = rreplace(question, '</br>', '\n', 5)
    question = '\n\nSC\n' + question
    new_html_string = new_html_string + question
html_string = new_html_string

with open('output.txt', 'w') as html_file:
        html_file.write(html_string)

