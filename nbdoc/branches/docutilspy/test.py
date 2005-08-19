from docutils import nodes

import notebook
from notebook import Section, Title, Subtitle, Paragraph

Title("This is the title")
Subtitle(".. with a subtitle")

introduction = Section() #BUG: this autoadds to document
introduction += Paragraph("The introduction starts with this.") #..dupe

background = Section() #same here
background += Paragraph("This paragraph starts the second section, background.")

#print str(document)

notebook.write()
