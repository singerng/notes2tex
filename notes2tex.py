# jinja2 code based off of http://eosrei.net/articles/2015/11/latex-templates-python-and-jinja2-generate-pdfs

import os
import re
import yaml
import jinja2
import tempfile
import shutil
import unicodedata

import argparse

parser = argparse.ArgumentParser(description='notes2tex: A utility for generating PDFs of handwritten notes.')
parser.add_argument('pdf_dir', help='directory of pdf files')
parser.add_argument('metadata_file', help='metadata file for course (yaml)')
parser.add_argument('--resize', help='resize (from OneNote)', action='store_true')
parser.set_defaults(resize=False)

args = parser.parse_args()

pdf_dir = os.path.abspath(args.pdf_dir)
template_file = "template.tex.j2"

with open(args.metadata_file) as yaml_file:
    course = yaml.load(yaml_file.read())
print(course)

latex_jinja_env = jinja2.Environment(
	block_start_string = '\BLOCK{',
	block_end_string = '}',
	variable_start_string = '\VAR{',
	variable_end_string = '}',
	comment_start_string = '\#{',
	comment_end_string = '}',
	line_statement_prefix = '%%',
	line_comment_prefix = '%#',
	trim_blocks = True,
	autoescape = False,
	loader = jinja2.FileSystemLoader(os.path.abspath('.'))
)

template = latex_jinja_env.get_template(template_file)

notes = []

for filename in os.listdir(pdf_dir):
	match = re.match("(\d+)\. (.+)\.pdf", filename)
	if match:
		notes.append({ 'num': match.group(1), 'title': unicodedata.normalize('NFC', match.group(2)), 'orig_filename': os.path.join(pdf_dir, match.group(0)) })

notes.sort(key=lambda x: int(x['num']))

tmp_dir = tempfile.mkdtemp()
tex_file = os.path.join(tmp_dir, "template.tex")

for note in notes:
    new_file = os.path.join(tmp_dir, "{}.pdf".format(note['num']))
    if args.resize:
        os.system("gs -o \"{}\" -sDEVICE=pdfwrite -dDEVICEWIDTHPOINTS=550 -dDEVICEHEIGHTPOINTS=600 -dFIXEDMEDIA -f \"{}\"".format(new_file, note['orig_filename']))
    else:
        shutil.copy2(note['orig_filename'], new_file)
    note['filename'] = new_file

print("Using tmp tex file", tex_file)

with open(tex_file, 'w') as tmp:
	tmp.write(template.render(course=course, notes=notes))

# Run twice to update TOC
os.system("pdflatex -output-directory={} -jobname=\"{}\" \"{}\"".format(tmp_dir, "output", tex_file))
os.system("pdflatex -output-directory={} -jobname=\"{}\" \"{}\"".format(tmp_dir, "output", tex_file))

shutil.copy2(os.path.join(tmp_dir, "output.pdf"), os.getcwd())
shutil.rmtree(tmp_dir)
