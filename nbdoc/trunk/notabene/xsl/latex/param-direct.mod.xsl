<?xml version="1.0"?>
<!--############################################################################
|	$Id: param-direct.mod.xsl,v 1.9 2004/08/12 05:17:01 j-devenish Exp $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:param name="latex.documentclass"/><xsl:param name="latex.maketitle">
		<xsl:text>{\maketitle</xsl:text>
		<xsl:call-template name="generate.latex.pagestyle"/>
		<xsl:text>\thispagestyle{empty}}
</xsl:text>
	</xsl:param><xsl:param name="latex.article.preamble.pre">
	</xsl:param><xsl:param name="latex.article.preamble.post">
	</xsl:param><xsl:param name="latex.article.varsets">
		<xsl:text>
\usepackage{anysize}
\marginsize{2cm}{2cm}{2cm}{2cm}
\renewcommand\floatpagefraction{.9}
\renewcommand\topfraction{.9}
\renewcommand\bottomfraction{.9}
\renewcommand\textfraction{.1}

		</xsl:text>
	</xsl:param><xsl:param name="latex.book.preamble.pre">
	</xsl:param><xsl:param name="latex.book.preamble.post">
	</xsl:param><xsl:param name="latex.book.varsets">
		<xsl:text>\usepackage{anysize}
</xsl:text>
		<xsl:text>\marginsize{3cm}{2cm}{1.25cm}{1.25cm}
</xsl:text>
	</xsl:param><xsl:param name="latex.book.begindocument">
		<xsl:text>\begin{document}
</xsl:text>
	</xsl:param><xsl:param name="latex.book.afterauthor">
		<xsl:text>% --------------------------------------------
</xsl:text>
		<xsl:text>\makeglossary
</xsl:text>
		<xsl:text>% --------------------------------------------
</xsl:text>
	</xsl:param><xsl:template name="latex.thead.row.entry">
		<xsl:apply-templates/>
	</xsl:template><xsl:template name="latex.tfoot.row.entry">
		<xsl:apply-templates/>
	</xsl:template><xsl:param name="latex.inline.monoseq.style">\frenchspacing\texttt</xsl:param><xsl:param name="latex.article.title.style">\textbf</xsl:param><xsl:param name="latex.book.article.title.style">\Large\textbf</xsl:param><xsl:param name="latex.book.article.header.style">\textsf</xsl:param><xsl:param name="latex.equation.caption.style"/><xsl:param name="latex.example.caption.style"/><xsl:param name="latex.figure.caption.style"/><xsl:param name="latex.figure.title.style"/><xsl:param name="latex.formalpara.title.style">\textbf</xsl:param><xsl:param name="latex.list.title.style">\sc</xsl:param><xsl:param name="latex.admonition.title.style">\bfseries \sc\large</xsl:param><xsl:param name="latex.procedure.title.style">\sc</xsl:param><xsl:param name="latex.segtitle.style">\em</xsl:param><xsl:param name="latex.step.title.style">\bf</xsl:param><xsl:param name="latex.table.caption.style"/><xsl:param name="latex.fancyhdr.lh">Left Header</xsl:param><xsl:param name="latex.fancyhdr.ch">Center Header</xsl:param><xsl:param name="latex.fancyhdr.rh">Right Header</xsl:param><xsl:param name="latex.fancyhdr.lf">Left Footer</xsl:param><xsl:param name="latex.fancyhdr.cf">Center Footer</xsl:param><xsl:param name="latex.fancyhdr.rf">Right Footer</xsl:param><xsl:param name="latex.pagestyle"/><xsl:param name="latex.hyperref.param.common">bookmarksnumbered,colorlinks,backref,bookmarks,breaklinks,linktocpage,plainpages=false</xsl:param><xsl:param name="latex.hyperref.param.pdftex">pdfstartview=FitH</xsl:param><!--
	what is the unicode option?
	--><xsl:param name="latex.hyperref.param.dvips"/><xsl:param name="latex.varioref.options">
		<xsl:if test="$latex.language.option!='none'">
			<xsl:value-of select="$latex.language.option"/>
		</xsl:if>
	</xsl:param><xsl:template name="latex.vpageref.options">on this page</xsl:template><xsl:param name="latex.fancyvrb.tabsize">3</xsl:param><xsl:template name="latex.fancyvrb.options"/><xsl:param name="latex.inputenc">latin1</xsl:param><xsl:param name="latex.fontenc"/><xsl:param name="latex.ucs.options"/><xsl:param name="latex.babel.language"/><xsl:param name="latex.bibwidelabel">
		<xsl:choose>
			<xsl:when test="$latex.biblioentry.style='ieee' or $latex.biblioentry.style='IEEE'">
				<xsl:text>123</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text>WIDELABEL</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:param><xsl:param name="latex.documentclass.common"/><xsl:param name="latex.documentclass.article">a4paper,10pt,twoside,twocolumn</xsl:param><xsl:param name="latex.documentclass.book">a4paper,10pt,twoside,openright</xsl:param><xsl:param name="latex.documentclass.pdftex"/><xsl:param name="latex.documentclass.dvips"/><xsl:param name="latex.admonition.imagesize">width=1cm</xsl:param><xsl:param name="latex.titlepage.file">title</xsl:param><xsl:param name="latex.document.font">palatino</xsl:param><xsl:param name="latex.override"/></xsl:stylesheet>
