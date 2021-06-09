import mammoth.documents
import mammoth.transforms
import re

fileobj="Test.docx"

def transform_run(run):
    return run#.copy(style_id="code", style_name="Code")

def rreplace(s, old, new, occurrence=-1):
 li = s.rsplit(old, occurrence)
 return new.join(li)

html_string = mammoth.convert_to_html(
    fileobj,
    #transform_document=mammoth.transforms.paragraph(transform_run),
    style_map=  """
                   b => b
                   i => i
    """
).value

############ Check for common mistakes #######
lists = re.compile('(</?ul>)|(</?li>)')
if lists.search(html_string):
    print("Found list items or list templates (Formatvorlagen)! Clear your input, please!")
    exit()

############# HTML-String RegEx ###############

# Handle paragraphs
paragraphs = re.compile('<p>(.*?)</p>')
html_string = paragraphs.sub(r'\1</br>', html_string)
# Remove everything until first group
html_string = re.compile(r'.*?(Group: .+?</br>)').sub(r'\1', html_string, 1)
# Find groups
groups = re.compile(r'(Group: .+?)</br>')
html_string = groups.sub(r'\n\n\n\1', html_string)
# Find Questiontags
#   print(re.compile(r'((<[\w/]*>)|\s+)*SC(<[\w/]*>)*\s*</br>').search(html_string).group())
html_string = re.compile(r'((<[\w/]*>)|\s+)*SC(<[\w/]*>)*\s*</br>').sub(r'\n\nSC\n', html_string)
# Find Questions
questions = re.compile(r'\n\nSC\n').split(html_string)
html_string = ""
for question in questions:
    # Find answers
    #answer = re.compile(r'(<[\w/]*?>)*(\d\t.*?)(<[\w/]*?>)*')
    answer = re.compile(r'(<[\w/]*?>)*(\d\t)')
    print(answer.findall(question))
    question = answer.sub(r'\n\2', question)
    question = rreplace(question, '\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
    html_string += question + '\n\nSC\n'
# Remove unnecessary SC at the end
html_string = rreplace(html_string, '\n\nSC\n', '', 1)

with open('output.txt', 'w') as html_file:
        html_file.write(html_string)