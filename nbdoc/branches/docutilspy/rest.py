import docutils, docutils.io
from docutils import nodes, frontend
from docutils.utils import Reporter
from docutils.writers.html4css1 import Writer

#from notebook import document #a singleton may live there

source = None
settings = frontend.OptionParser().get_default_values()
settings.xml_declaration = False
settings.embed_stylesheet = False
settings.stylesheet_path = False
settings.stylesheet = None
settings.initial_header_level = "1" 
reporter = Reporter(source, settings.report_level, settings.halt_level,
                    stream=settings.warning_stream, debug=settings.debug,
                    encoding=settings.error_encoding,
                    error_handler=settings.error_encoding_error_handler)
document = nodes.document(settings, reporter)

title = nodes.title(text="This is the title")
subtitle = nodes.subtitle(text=".. with a subtitle")

introduction = nodes.section()
start = nodes.paragraph(text="The introduction starts with this.")
introduction += start

background = nodes.section()
background += nodes.paragraph(text="This paragraph starts the second section, background.")

document += [title, subtitle, introduction, background]

#print str(document)

out = docutils.io.FileOutput()
out.encoding = 'unicode'
w = Writer()
w.write(document, out)
