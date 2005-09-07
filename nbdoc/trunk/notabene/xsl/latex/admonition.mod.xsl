<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: admonition.mod.xsl,v 1.15 2004/08/12 05:33:43 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:param name="latex.admonition.environment">
		<xsl:text>% ----------------------------------------------
</xsl:text>
		<xsl:text>% Define a new LaTeX environment (adminipage)
</xsl:text>
		<xsl:text>% ----------------------------------------------
</xsl:text>
		<xsl:text>\newenvironment{admminipage}%
</xsl:text>
		<xsl:text>{ % this code corresponds to the \begin{adminipage} command
</xsl:text>
		<xsl:text> \begin{Sbox}%
</xsl:text>
		<xsl:text> \begin{minipage}%
</xsl:text>
		<xsl:text>} %done
</xsl:text>
		<xsl:text>{ % this code corresponds to the \end{adminipage} command
</xsl:text>
		<xsl:text> \end{minipage}
</xsl:text>
		<xsl:text> \end{Sbox}
</xsl:text>
		<xsl:text> \fbox{\TheSbox}
</xsl:text>
		<xsl:text>} %done
</xsl:text>
		<xsl:text>% ----------------------------------------------
</xsl:text>
		<xsl:text>% Define a new LaTeX length (admlength)
</xsl:text>
		<xsl:text>% ----------------------------------------------
</xsl:text>
		<xsl:text>\newlength{\admlength}
</xsl:text>
		<xsl:text>% ----------------------------------------------
</xsl:text>
		<xsl:text>% Define a new LaTeX environment (admonition)
</xsl:text>
		<xsl:text>% With 2 parameters:
</xsl:text>
		<xsl:text>% #1 The file (e.g. note.pdf)
</xsl:text>
		<xsl:text>% #2 The caption
</xsl:text>
		<xsl:text>% ----------------------------------------------
</xsl:text>
		<xsl:text>\newenvironment{admonition}[2] 
</xsl:text>
		<xsl:text>{ % this code corresponds to the \begin{admonition} command
</xsl:text>
		<xsl:text> \hspace{0mm}\newline\hspace*\fill\newline
</xsl:text>
		<xsl:text> \noindent
</xsl:text>
		<xsl:text> \setlength{\fboxsep}{5pt}
</xsl:text>
		<xsl:text> \setlength{\admlength}{\linewidth}
</xsl:text>
		<xsl:text> \addtolength{\admlength}{-10\fboxsep}
</xsl:text>
		<xsl:text> \addtolength{\admlength}{-10\fboxrule}
</xsl:text>
		<xsl:text> \admminipage{\admlength}
</xsl:text>
		<xsl:text> {</xsl:text>
		<xsl:value-of select="$latex.admonition.title.style"/>
		<xsl:text>{#2}}</xsl:text>
		<xsl:text> \newline
</xsl:text>
		<xsl:text> \\[1mm]
</xsl:text>
		<xsl:text> \sffamily
</xsl:text>
		<!--
		If we cannot find the admon.graphics.path;
		Comment out the next line (\includegraphics).
		This tactic is to avoid deleting the \includegraphics
		altogether, as that could confuse a person trying to
		find the use of parameter #1 in the environment.
		-->
		<xsl:if test="$admon.graphics.path=''">
			<xsl:text>%</xsl:text>
		</xsl:if>
		<xsl:text> \includegraphics[</xsl:text> <xsl:value-of select="$latex.admonition.imagesize"/> <xsl:text>]{#1}
</xsl:text>
		<xsl:text> \addtolength{\admlength}{-1cm}
</xsl:text>
		<xsl:text> \addtolength{\admlength}{-20pt}
</xsl:text>
		<xsl:text> \begin{minipage}[lt]{\admlength}
</xsl:text>
		<xsl:text> \parskip=0.5\baselineskip \advance\parskip by 0pt plus 2pt
</xsl:text>
		<xsl:text>} %done
</xsl:text>
		<xsl:text>{ % this code corresponds to the \end{admonition} command
</xsl:text>
		<xsl:text> \vspace{5mm} 
</xsl:text>
		<xsl:text> \end{minipage}
</xsl:text>
		<xsl:text> \endadmminipage
</xsl:text>
		<xsl:text> \vspace{.5em}
</xsl:text>
		<xsl:text> \par
</xsl:text>
		<xsl:text>}
</xsl:text>
	</xsl:param><xsl:template name="admon.graphic">
		<xsl:param name="name" select="local-name(.)"/>
		<xsl:choose>
			<xsl:when test="$name='note'">note</xsl:when>
			<xsl:when test="$name='warning'">warning</xsl:when>
			<xsl:when test="$name='caution'">caution</xsl:when>
			<xsl:when test="$name='tip'">tip</xsl:when>
			<xsl:when test="$name='important'">important</xsl:when>
			<xsl:otherwise>note</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="note|important|warning|caution|tip">
		<xsl:call-template name="map.begin">
			<xsl:with-param name="keyword">admonition</xsl:with-param>
			<xsl:with-param name="string">
				<xsl:text>{</xsl:text>
				<xsl:value-of select="$admon.graphics.path"/><xsl:text>/</xsl:text>
				<xsl:call-template name="admon.graphic"/>
				<xsl:text>}{</xsl:text>
				<xsl:choose>
					<xsl:when test="title and $latex.apply.title.templates.admonitions='1'">
						<xsl:call-template name="extract.object.title">
							<xsl:with-param name="object" select="."/>
						</xsl:call-template>
					</xsl:when>
					<xsl:otherwise>
						<xsl:call-template name="gentext.element.name"/>
					</xsl:otherwise>
				</xsl:choose>
				<xsl:text>}</xsl:text>
			</xsl:with-param>
		</xsl:call-template>
		<xsl:call-template name="content-templates"/>
		<xsl:call-template name="map.end">
			<xsl:with-param name="keyword">admonition</xsl:with-param>
		</xsl:call-template>
	</xsl:template></xsl:stylesheet>
