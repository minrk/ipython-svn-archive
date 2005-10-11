<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: index.mod.xsl,v 1.21 2004/08/12 05:47:32 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<!-- Our key for ranges --><xsl:key name="indexterm-range" match="indexterm[@class='startofrange']" use="@id"/><xsl:template match="index|setindex">
		<xsl:variable name="preamble" select="node()[not(self::indexinfo or self::setindexinfo or self::title or self::subtitle or self::titleabbrev or self::indexdiv or self::indexentry)]"/>
      <xsl:text>\setlength\saveparskip\parskip
</xsl:text>
      <xsl:text>\setlength\saveparindent\parindent
</xsl:text>
		<xsl:text>\begin{dbtolatexindex}{</xsl:text>
		<xsl:call-template name="generate.label.id"/>
		<xsl:text>}{</xsl:text>
		<xsl:call-template name="extract.object.title">
			<xsl:with-param name="object" select="."/>
			<!-- perhaps we *should* define \indexname according to
			gentext.element.name, but instead we let LaTeX/Babel handle it. -->
		</xsl:call-template>
		<xsl:text>}
</xsl:text>
		<xsl:text>\setlength\tempparskip\parskip \setlength\tempparindent\parindent
</xsl:text>
		<xsl:text>\parskip\saveparskip \parindent\saveparindent
</xsl:text>
		<xsl:text>\noindent </xsl:text><!-- &#10; -->
		<xsl:apply-templates select="$preamble"/>
		<xsl:call-template name="map.begin"/>
		<xsl:text>\parskip\tempparskip
</xsl:text>
		<xsl:text>\parindent\tempparindent
</xsl:text>
		<xsl:text>\makeatletter\@input@{\jobname.ind}\makeatother
</xsl:text>
		<xsl:call-template name="map.end"/>
		<xsl:text>\end{dbtolatexindex}
</xsl:text>
	</xsl:template><xsl:template name="latex.preamble.essential.index">
		<xsl:text>
			
\makeindex
% index labeling helper
\newif\ifdocbooktolatexprintindex\docbooktolatexprintindextrue
\let\dbtolatex@@theindex\theindex
\let\dbtolatex@@endtheindex\endtheindex
\@ifundefined{@openrighttrue}{\newif\if@openright}{}
\def\theindex{\relax}
\def\endtheindex{\relax}
\newenvironment{dbtolatexindex}[2]
   {
\if@openright\cleardoublepage\else\clearpage\fi
\let\dbtolatex@@indexname\indexname
\def\dbtolatex@current@indexname{#2}
\ifx\dbtolatex@current@indexname\@empty                                                                                             \def\dbtolatex@current@indexname{\dbtolatex@@indexname}
\fi
\def\dbtolatex@indexlabel{%
 \ifnum \c@secnumdepth &gt;\m@ne \ifx\c@chapter\undefined\refstepcounter{section}\else\refstepcounter{chapter}\fi\fi%
 \label{#1}\hypertarget{#1}{\dbtolatex@current@indexname}%
 \global\docbooktolatexprintindexfalse}
\def\indexname{\ifdocbooktolatexprintindex\dbtolatex@indexlabel\else\dbtolatex@current@indexname\fi}
\dbtolatex@@theindex
   }
   {
\dbtolatex@@endtheindex\let\indexname\dbtolatex@@indexname
   }

\newlength\saveparskip \newlength\saveparindent
\newlength\tempparskip \newlength\tempparindent

		</xsl:text>
	</xsl:template><!--
	<xsl:template match="index/title">
		<xsl:call-template name="label.id"> <xsl:with-param name="object" select=".."/> </xsl:call-template>
	</xsl:template>

<xsl:template match="indexdiv">
	<xsl:apply-templates/>
</xsl:template>

<xsl:template match="indexdiv/title">
	<xsl:call-template name="label.id"> <xsl:with-param name="object" select=".."/> </xsl:call-template>
</xsl:template>

	<xsl:template match="primary|secondary|tertiary|see|seealso"/>

--><!-- INDEX TERM CONTENT MODEL
	IndexTerm ::=
	(Primary,
	((Secondary,
	((Tertiary,
	(See|SeeAlso+)?)|
	See|SeeAlso+)?)|
	See|SeeAlso+)?)
	--><xsl:template match="indexterm">
		<xsl:if test="$latex.generate.indexterm='1'">
			<xsl:variable name="idxterm">
				<xsl:apply-templates mode="indexterm"/>
			</xsl:variable>

			<xsl:if test="@class and @zone">
				<xsl:message terminate="yes">Error: Only one attribute (@class or @zone) is in indexterm possible!</xsl:message>
			</xsl:if>

			<xsl:if test="not(preceding-sibling::para) and following-sibling::para">
				<xsl:text>
</xsl:text>
			</xsl:if>

			<xsl:choose>
				<xsl:when test="@class='startofrange'">
					<xsl:text>\index{</xsl:text>
					<xsl:value-of select="$idxterm"/>
					<xsl:text>|(}</xsl:text>
				</xsl:when>
				<xsl:when test="@class='endofrange'">
					<xsl:choose>
						<xsl:when test="count(key('indexterm-range',@startref)) = 0">
							<xsl:message terminate="yes"><xsl:text>Error: No indexterm with </xsl:text>
							<xsl:text>id='</xsl:text><xsl:value-of select="@startref"/>
							<xsl:text>' found!</xsl:text>
							<xsl:text>  Check your attributs id/startref in your indexterms!</xsl:text>
							</xsl:message>
						</xsl:when>
						<xsl:otherwise>
							<xsl:variable name="thekey" select="key('indexterm-range',@startref)"/>
							<xsl:for-each select="$thekey[1]">
								<xsl:text>\index{</xsl:text>
								<xsl:apply-templates mode="indexterm"/>
								<xsl:text>|)}</xsl:text>
							</xsl:for-each>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:when>
				<xsl:otherwise>
					<xsl:text>\index{</xsl:text>
					<xsl:value-of select="$idxterm"/>
					<xsl:text>}</xsl:text>
				</xsl:otherwise>
			</xsl:choose>
			<xsl:if test="not(preceding-sibling::para) and following-sibling::para">
				<xsl:text>%</xsl:text><!-- gobble following para's initial newline -->
			</xsl:if>
			<xsl:if test="preceding-sibling::para">
				<xsl:text>
</xsl:text>
			</xsl:if>
		</xsl:if>
	</xsl:template><xsl:template match="*" mode="indexterm">
		<xsl:message>WARNING: Element '<xsl:value-of select="local-name()"/>' in indexterm not supported and skipped!</xsl:message>
	</xsl:template><!--
	<xsl:template match="acronym|foreignphrase" mode="indexterm">
		<xsl:apply-templates mode="indexterm"/>
	</xsl:template>
	--><xsl:template match="primary" mode="indexterm">
		<xsl:call-template name="index.subterm"/>
	</xsl:template><xsl:template match="secondary|tertiary" mode="indexterm">
		<xsl:text>!</xsl:text>
		<xsl:call-template name="index.subterm"/>
	</xsl:template><xsl:template name="index.subterm">
		<xsl:variable name="style" select="processing-instruction('latex-index-style')"/>
		<xsl:choose>
			<xsl:when test="@sortas!=''">
				<xsl:variable name="string">
					<xsl:call-template name="scape-indexterm">
						<xsl:with-param name="string" select="@sortas"/>
					</xsl:call-template>
				</xsl:variable>
				<xsl:variable name="content">
					<xsl:call-template name="scape-indexterm">
						<xsl:with-param name="string" select="."/>
					</xsl:call-template>
				</xsl:variable>
				<xsl:value-of select="normalize-space($string)"/>
				<xsl:text>@{</xsl:text>
				<xsl:value-of select="$style"/>
				<xsl:text>{</xsl:text>
				<xsl:value-of select="normalize-space($content)"/>
				<xsl:text>}}</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<xsl:variable name="string">
					<xsl:call-template name="scape-indexterm">
						<xsl:with-param name="string" select="."/>
					</xsl:call-template>
				</xsl:variable>
				<xsl:value-of select="normalize-space($string)"/>
				<xsl:if test="$style!=''">
					<xsl:text>@{</xsl:text>
					<xsl:value-of select="$style"/>
					<xsl:text>{</xsl:text>
					<xsl:value-of select="normalize-space($string)"/>
					<xsl:text>}}</xsl:text>
				</xsl:if>
			</xsl:otherwise>
		</xsl:choose>
		<!--
		<xsl:apply-templates mode="indexterm"/>
		-->
	</xsl:template><xsl:template match="see|seealso" mode="indexterm">
		<xsl:text>|textit{</xsl:text>
		<xsl:call-template name="gentext.element.name"/>
		<xsl:text>} {</xsl:text>
		<xsl:apply-templates/>
		<!--
		<xsl:apply-templates mode="indexterm"/>
		-->
		<xsl:text>} </xsl:text>
	</xsl:template><xsl:template match="indexentry|primaryie|secondaryie|tertiaryie|seeie|seealsoie"/></xsl:stylesheet>
