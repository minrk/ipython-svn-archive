<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: footnote.mod.xsl,v 1.10 2004/01/02 06:45:25 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="footnote">
		<xsl:call-template name="label.id"/>
		<xsl:text>\begingroup\catcode`\#=12\footnote{</xsl:text>
		<xsl:apply-templates/>
		<xsl:text>}\endgroup\docbooktolatexmakefootnoteref{</xsl:text>
		<xsl:call-template name="generate.label.id"/>
		<xsl:text>}</xsl:text>
	</xsl:template><xsl:template name="latex.preamble.essential.footnote">
		<xsl:text>
			
% --------------------------------------------
% A way to honour &lt;footnoteref&gt;s
% Blame j-devenish (at) users.sourceforge.net
% In any other LaTeX context, this would probably go into a style file.
\newcommand{\docbooktolatexusefootnoteref}[1]{\@ifundefined{@fn@label@#1}%
  {\hbox{\@textsuperscript{\normalfont ?}}%
    \@latex@warning{Footnote label `#1' was not defined}}%
  {\@nameuse{@fn@label@#1}}}
\newcommand{\docbooktolatexmakefootnoteref}[1]{%
  \protected@write\@auxout{}%
    {\global\string\@namedef{@fn@label@#1}{\@makefnmark}}%
  \@namedef{@fn@label@#1}{\hbox{\@textsuperscript{\normalfont ?}}}%
  }

		</xsl:text>
	</xsl:template><xsl:template name="generate.ulink.in.footnote">
		<xsl:param name="hyphenation"/>
		<xsl:param name="url"/>
		<xsl:call-template name="label.id"/>
		<xsl:text>\begingroup\catcode`\#=12\footnote{</xsl:text>
		<xsl:call-template name="generate.typeset.url">
			<xsl:with-param name="hyphenation" select="$hyphenation"/>
			<xsl:with-param name="url" select="$url"/>
		</xsl:call-template>
		<xsl:text>}\endgroup\docbooktolatexmakefootnoteref{</xsl:text>
		<xsl:call-template name="generate.label.id"/>
		<xsl:text>}</xsl:text>
	</xsl:template><xsl:template match="footnoteref">
		<xsl:variable name="footnote" select="key('id',@linkend)"/>
		<xsl:text>\docbooktolatexusefootnoteref{</xsl:text>
		<xsl:value-of select="@linkend"/>
		<xsl:text>}</xsl:text>
	</xsl:template></xsl:stylesheet>
