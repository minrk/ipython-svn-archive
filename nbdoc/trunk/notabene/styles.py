# ain't no way I'm reimplementing that crap until we have to
from matplotlib import colors

from lxml import etree as ET

import os
XSLDIR = os.path.join(os.path.split(__file__)[0], 'xsl')

if not os.path.exists(os.path.join(XSLDIR, 'xhtml', 'docbook.xsl')):
    raise RuntimeError("XSLT files not in the right location")


class TextStyle(object):
    weights_latex = {"bold": "bfseries",
                    }
    def __init__(self, name, color=None, weight=None):
        self.name = name
        
        if color is not None:
            self.color = colors.colorConverter.to_rgb(color)
        else:
            self.color = None

        self.weight = weight

    def as_css(self):
        lines = []
        if self.color is not None:
            lines.append("    color: %s;" % colors.rgb2hex(self.color))
        if self.weight is not None:
            lines.append("    font-weight: %s;" % self.weight)

        if lines:
            return "span.%s{\n%s\n}\n" % (self.name, '\n'.join(lines))

        else:
            return ""

    def as_latex(self):
        cmds = []
        if self.color is not None:
            cmds.append(r"\color[rgb]{%s,%s,%s}" % self.color)
        if self.weight not in (None, "normal"):
            cmds.append(r"\%s" % self.weights_latex[self.weight])

        cmd = "\\newcommand{\\%s}[1]{{%s#1}}" % (self.cmd_name(), "".join(cmds))
        return cmd

    def cmd_name(self):
        return self.name.replace('_', '').replace('2', 'two')

base_css = """
body {
    background-color: #FFFFFF;
    color: #000;
    font-family: Verdana;
    font-size: 12px;
    line-height: 20px;
}

tt,pre {
    font-family: Lucida Console,Courier New,Courier,monotype;
    font-size: 100%
}

pre.programlisting {
    background-color: #EEE;
    white-space:pre;
    color:#111111;
    padding: 0 0 0 0;
    width:100%;
    font-size: 10pt;
}

div.ipy_block {
    background-color: #EEE;
    display: table;
    margin-left: 10pt;
    padding-left: 1em;
    padding-right: 1em;
}
div.ipy_in_prompt {
    background-color: #EEE;
    max-width: 10em;
    display: table-cell;
}
div.ipy_out_prompt {
    background-color: #EEE;
    max-width: 10em;
    display: table-cell;
}
div.ipy_code {
    background-color: #EEE;
    display: table-cell;
}
div.ipy_input_bundle {
    background-color: #EEE;
    display: table-row;
    margin: 0;
    padding: 0;
}
div.ipy_output {
    background-color: #EEE;
    display: table-cell;
}
div.ipy_output_bundle {
    background-color: #EEE;
    display: table-row;
    margin: 0;
    padding: 0;
}
"""

class Style(object):
    nsmap = {"xsl": "http://www.w3.org/1999/XSL/Transform",
            }
    def __init__(self, styles_dict):
        self.styles_dict = styles_dict

    def latex_xsl(self):
        sheet = ET.Element("xsl:stylesheet", version="1.0", nsmap=self.nsmap)

        # configure this later
        ET.SubElement(sheet, "xsl:import",
                      href=XSLDIR+"/latex/docbook.xsl")

        # turn on fancyvrb
        fancyvrb = ET.SubElement(sheet, "xsl:param", name="latex.use.fancyvrb")
        fancyvrb.text = "1"
        fvopt = ET.SubElement(sheet, "xsl:template", name="latex.fancyvrb.options")
        fvopt.text = r",commandchars=\\\{\}"

        docclass = ET.SubElement(sheet, "xsl:param",
            name="latex.documentclass.article")
        docclass.text = "letterpaper,10pt,twoside"

        amble = ET.SubElement(sheet, "xsl:param",
            name="latex.article.preamble.post")
        amble.text = '\n'.join(x.as_latex() for x in self.styles_dict.itervalues())
        amble.text = '\n%s\n' % amble.text

        # and again for book
        amble = ET.SubElement(sheet, "xsl:param",
            name="latex.book.preamble.post")
        amble.text = '\n'.join(x.as_latex() for x in self.styles_dict.itervalues())
        amble.text = '\n%s\n' % amble.text

        # change to English and UTF-8
        lang = ET.SubElement(sheet, "xsl:variable", name="l10n.gentext.default.language")
        lang.text = "en"
        ET.SubElement(sheet, "xsl:variable", name="latex.documentclass.common")
        ET.SubElement(sheet, "xsl:variable", name="latex.babel.language")
        encoding = ET.SubElement(sheet, "xsl:output", method="text",
            encoding="UTF-8", indent="yes")

        # add the templates for syntax-highlighting
        for textstyle in self.styles_dict.itervalues():
            template = ET.SubElement(sheet, "xsl:template",
                match='phrase[@role="%s"]' % textstyle.name,
                mode="latex.verbatim")
            template.text = '\\%s{' % textstyle.cmd_name()
            value = ET.SubElement(template, "xsl:value-of", select="./text()")
            value.tail = '}'


        # lxml's namespace handling isn't *quite* as good as I was hoping
        sheet = ET.ElementTree(ET.fromstring(ET.tostring(sheet)))
        return sheet

    def html_css(self):
        newcss = "".join(x.as_css() for x in self.styles_dict.itervalues())
        return "\n".join((base_css, newcss))

    def html_xsl(self):
        sheet = ET.Element("xsl:stylesheet", version="1.0", nsmap=self.nsmap)

        ET.SubElement(sheet, "xsl:import",
            href = XSLDIR + "/xhtml/docbook.xsl")

        css = ET.SubElement(sheet, "xsl:template", name="user.head.content")
        css_style = ET.SubElement(css, "style", type="text/css")
        comment = ET.SubElement(css_style, "xsl:comment")
        comment.text = self.html_css()

        # lxml's namespace handling isn't *quite* as good as I was hoping
        sheet = ET.ElementTree(ET.fromstring(ET.tostring(sheet)))
        return sheet

    @staticmethod
    def escape_latex(text, commands=r"\{}"):
        for c in commands:
            text = text.replace(c, "\\" + c)
        return text

    def fo_xsl(self):
        sheet = ET.Element("xsl:stylesheet", version="1.0", nsmap=self.nsmap)
        ET.SubElement(sheet, "xsl:import",
            href = XSLDIR + "/fo/antont-docbook.xsl")
        # lxml's namespace handling isn't *quite* as good as Robert was hoping
        sheet = ET.ElementTree(ET.fromstring(ET.tostring(sheet)))
        return sheet


LightBGStyle = Style({
    'py_keyword': TextStyle("py_keyword", color="#C00000"),
    'py_string': TextStyle("py_string", color="#004080"),
    'py_comment': TextStyle("py_comment", color="#008000"),
    'py_identifier': TextStyle("py_identifier", color="#0000C0"),
    'ipy_in_prompt': TextStyle("ipy_in_prompt", color="#0000FF", weight="bold"),
    'ipy_in_number': TextStyle("ipy_in_number", color="#3333FF", weight="bold"),
    'ipy_in_prompt2': TextStyle("ipy_in_prompt2", color="#0000FF", weight="bold"),
    'ipy_out_prompt': TextStyle("ipy_out_prompt", color="#FF0000", weight="bold"),
    'ipy_out_number': TextStyle("ipy_out_number", color="#FF3333", weight="bold"),
    'ipy_stderr_prompt': TextStyle("ipy_stderr_prompt", color="#FF0000", weight="bold"),
    'ipy_stderr': TextStyle("ipy_stderr", color="#440000", weight="bold"),
    'ipy_fig_prompt': TextStyle("ipy_fig_prompt", weight="bold"),
})


