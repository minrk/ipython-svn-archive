<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: book-article.mod.xsl,v 1.43 2004/08/12 06:18:58 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="book">
		<!-- book:1: generate.latex.book.preamble -->
		<xsl:call-template name="generate.latex.book.preamble"/>
		<!-- book:2: output title information     -->
		<xsl:text>\title{</xsl:text>
			<xsl:apply-templates select="title|bookinfo/title"/>
			<xsl:apply-templates select="subtitle|bookinfo/subtitle"/>
		<xsl:text>}
</xsl:text>
		<!-- book:3: output author information     -->
		<xsl:text>\author{</xsl:text>
		<xsl:choose>
			<xsl:when test="bookinfo/authorgroup">
				<xsl:apply-templates select="bookinfo/authorgroup"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:for-each select="bookinfo">
					<xsl:call-template name="authorgroup"/>
				</xsl:for-each>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:text>}
</xsl:text>
		<!-- book:4: dump any preamble after author  -->
		<xsl:value-of select="$latex.book.afterauthor"/>
		<!-- book:5: set some counters  -->
		<xsl:text>
\setcounter{tocdepth}{</xsl:text><xsl:value-of select="$toc.section.depth"/><xsl:text>}
</xsl:text>
		<xsl:text>
\setcounter{secnumdepth}{</xsl:text><xsl:value-of select="$section.depth"/><xsl:text>}
</xsl:text>
		<!-- book:6: dump the begin document command  -->
		<xsl:value-of select="$latex.book.begindocument"/>
		<!-- book:7: include external Cover page if specified -->
		<xsl:if test="$latex.titlepage.file != ''">
			<xsl:text>
\InputIfFileExists{</xsl:text><xsl:value-of select="$latex.titlepage.file"/>
			<xsl:text>}{\typeout{WARNING: Using cover page </xsl:text>
			<xsl:value-of select="$latex.titlepage.file"/>
			<xsl:text>}}</xsl:text>
		</xsl:if>
		<!-- book:7b: maketitle and set up pagestyle -->
		<xsl:value-of select="$latex.maketitle"/>
		<!-- book:8: - APPLY TEMPLATES -->
		<xsl:apply-templates select="bookinfo"/>
		<xsl:call-template name="content-templates-rootid"/>
		<!-- book:9:  call map.end -->
		<xsl:call-template name="map.end"/>
	</xsl:template><xsl:template match="book/title">\bfseries <xsl:apply-templates/></xsl:template><xsl:template match="book/subtitle">\\[12pt]\normalsize <xsl:apply-templates/></xsl:template><xsl:template match="book/bookinfo/title">\bfseries <xsl:apply-templates/></xsl:template><xsl:template match="book/bookinfo/subtitle">\\[12pt]\normalsize <xsl:apply-templates/></xsl:template><xsl:template match="book/bookinfo">
		<xsl:apply-templates select="revhistory"/>
		<xsl:if test="copyright">
			<xsl:call-template name="generate.bookinfo.copyright"/>
		</xsl:if>
		<xsl:apply-templates select="keywordset"/>
		<xsl:apply-templates select="legalnotice"/>
		<xsl:apply-templates select="abstract"/>
	</xsl:template><xsl:template name="generate.bookinfo.copyright">
		<xsl:text>\begin{center}</xsl:text>
		<xsl:apply-templates select="copyright"/>
		<xsl:text>\end{center}
</xsl:text>
	</xsl:template><xsl:template match="bookinfo/copyright">
		<xsl:call-template name="copyright"/>
		<xsl:if test="following-sibling::copyright">
			<xsl:text>\\
</xsl:text>
		</xsl:if>
	</xsl:template><!--
	    <formalpara><title>Tasks</title>
		<itemizedlist>
		    <listitem><para>Calls <literal>generate.latex.article.preamble</literal>.</para></listitem>
		    <listitem><para>Outputs \title, \author, \date, getting the information from its children.</para></listitem>
		    <listitem><para>Calls <literal>latex.article.begindocument</literal>.</para></listitem>
		    <listitem><para>Calls <literal>latex.article.maketitle.</literal></para></listitem>
		    <listitem><para>Applies templates.</para></listitem>
		    <listitem><para>Calls <literal>latex.article.end</literal> template.</para></listitem>
		</itemizedlist>
	    </formalpara>
		--><xsl:template match="book/article">
		<xsl:text>
\makeatletter\if@openright\cleardoublepage\else\clearpage\fi</xsl:text>
		<xsl:call-template name="generate.latex.pagestyle"/>
		<xsl:text>\makeatother
</xsl:text>	
		<!-- Get and output article title -->
		<xsl:variable name="article.title">
			<xsl:choose>
				<xsl:when test="./title"> 
					<xsl:apply-templates select="./title"/>
				</xsl:when>
				<xsl:when test="./articleinfo/title">
					<xsl:apply-templates select="./articleinfo/title"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:apply-templates select="./artheader/title"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:text>\begin{center}{</xsl:text>
		<xsl:value-of select="$latex.book.article.title.style"/>
		<xsl:text>{</xsl:text>
		<xsl:value-of select="$article.title"/>
		<xsl:text>}}\par
</xsl:text>
		<!-- Display date information -->
		<xsl:variable name="article.date">
			<xsl:apply-templates select="./artheader/date|./articleinfo/date"/>
		</xsl:variable>
		<xsl:if test="$article.date!=''">
			<xsl:text>{</xsl:text>
			<xsl:value-of select="$article.date"/>
			<xsl:text>}\par
</xsl:text>
		</xsl:if>
		<!-- Display author information -->
		<xsl:text>{</xsl:text>
		<xsl:value-of select="$latex.book.article.header.style"/>
		<xsl:text>{</xsl:text>
		<xsl:choose>
			<xsl:when test="articleinfo/authorgroup">
				<xsl:apply-templates select="articleinfo/authorgroup"/>
			</xsl:when>
			<xsl:when test="artheader/authorgroup">
				<xsl:apply-templates select="artheader/authorgroup"/>
			</xsl:when>
			<xsl:when test="articleinfo/author">
				<xsl:for-each select="artheader">
					<xsl:call-template name="authorgroup"/>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="artheader/author">
				<xsl:for-each select="artheader">
					<xsl:call-template name="authorgroup"/>
				</xsl:for-each>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name="authorgroup"/>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:text>}}\par
</xsl:text>
		<xsl:apply-templates select="artheader|articleinfo" mode="article.within.book"/>
		<xsl:text>\end{center}
</xsl:text>
		<xsl:call-template name="content-templates"/>
	</xsl:template><xsl:template match="article">
		<xsl:call-template name="generate.latex.article.preamble"/>
		<xsl:text>
\setcounter{tocdepth}{</xsl:text><xsl:value-of select="$toc.section.depth"/><xsl:text>}
</xsl:text>
		<xsl:text>
\setcounter{secnumdepth}{</xsl:text><xsl:value-of select="$section.depth"/><xsl:text>}
</xsl:text>
	<!-- Get and output article title -->
		<xsl:variable name="article.title">
			<xsl:choose>
				<xsl:when test="./title"> 
					<xsl:apply-templates select="./title"/>
				</xsl:when>
				<xsl:when test="./articleinfo/title">
					<xsl:apply-templates select="./articleinfo/title"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:apply-templates select="./artheader/title"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:text>\title{</xsl:text>
		<xsl:value-of select="$latex.article.title.style"/>
		<xsl:text>{</xsl:text>
		<xsl:value-of select="$article.title"/>
		<xsl:text>}}
</xsl:text>
		<!-- Display date information -->
		<xsl:variable name="article.date">
			<xsl:apply-templates select="./artheader/date|./articleinfo/date"/>
		</xsl:variable>
		<xsl:if test="$article.date!=''">
			<xsl:text>\date{</xsl:text>
			<xsl:value-of select="$article.date"/>
			<xsl:text>}
</xsl:text>
		</xsl:if>
		<!-- Display author information -->
		<xsl:text>\author{</xsl:text>
		<xsl:choose>
			<xsl:when test="articleinfo/authorgroup">
				<xsl:apply-templates select="articleinfo/authorgroup"/>
			</xsl:when>
			<xsl:when test="artheader/authorgroup">
				<xsl:apply-templates select="artheader/authorgroup"/>
			</xsl:when>
			<xsl:when test="articleinfo/author">
				<xsl:for-each select="artheader">
					<xsl:call-template name="authorgroup"/>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="artheader/author">
				<xsl:for-each select="artheader">
					<xsl:call-template name="authorgroup"/>
				</xsl:for-each>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name="authorgroup"/>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:text>}
</xsl:text>
		<!-- Display  begindocument command -->
		<xsl:call-template name="map.begin"/>
		<xsl:value-of select="$latex.maketitle"/>
		<xsl:apply-templates select="artheader|articleinfo" mode="standalone.article"/>
		<xsl:call-template name="content-templates-rootid"/>
		<xsl:call-template name="map.end"/>
    </xsl:template><xsl:template match="articleinfo/date|artheader/date">
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="article/artheader|article/articleinfo" mode="standalone.article">
		<xsl:apply-templates select="keywordset"/>
		<xsl:apply-templates select="legalnotice"/>
		<xsl:apply-templates select="abstract"/>
	</xsl:template><xsl:template match="article/artheader|article/articleinfo"/><xsl:template match="article/artheader|article/articleinfo" mode="article.within.book">
		<xsl:apply-templates select="abstract"/>
		<xsl:apply-templates select="legalnotice"/>
	</xsl:template><xsl:template match="legalnotice">
		<xsl:text>
{\if@twocolumn
</xsl:text>
			<xsl:text>\noindent\small\textit{
</xsl:text>
			<xsl:call-template name="legalnotice.title"/>
			<xsl:text>}\/\bfseries---$\!$%
</xsl:text>
		<xsl:text>\else
</xsl:text>
			<xsl:text>\noindent\begin{center}\small\bfseries 
</xsl:text>
			<xsl:call-template name="legalnotice.title"/>
			<xsl:text>\end{center}\begin{quote}\small
</xsl:text>
		<xsl:text>\fi
</xsl:text>
		<xsl:call-template name="content-templates"/>
		<xsl:text>\vspace{0.6em}\par\if@twocolumn\else\end{quote}\fi}
</xsl:text>
		<!--
		<xsl:text>\normalsize\rmfamily&#10;</xsl:text>
		-->
	</xsl:template><xsl:template name="legalnotice.title">
		<xsl:param name="title" select="blockinfo/title|title"/>
		<xsl:choose>
			<xsl:when test="count($title)&gt;0">
				<xsl:apply-templates select="$title[1]"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name="gentext">
					<xsl:with-param name="key">legalnotice</xsl:with-param>
				</xsl:call-template>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="toc" name="toc">
		<xsl:text>
</xsl:text>
		<xsl:call-template name="latex.noparskip"/>
		<xsl:choose>
			<xsl:when test="$latex.use.hyperref=1">
				<xsl:text>
\makeatletter
\def\dbtolatex@contentsid{</xsl:text>
				<xsl:call-template name="generate.label.id"/>
				<xsl:text>}
\def\dbtolatex@@contentsname{</xsl:text>
				<xsl:variable name="title">
					<xsl:call-template name="extract.object.title">
						<xsl:with-param name="object" select="."/>
					</xsl:call-template>
				</xsl:variable>
				<xsl:choose>
					<xsl:when test="$title=''">
						<xsl:text>\latex@@contentsname</xsl:text>
						<!-- we *should* define \contentsname according to
						gentext.element.name, but instead we let Babel handle it. -->
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="$title"/>
					</xsl:otherwise>
				</xsl:choose>
				<xsl:text>}
\let\latex@@contentsname\contentsname
\newif\ifdocbooktolatexcontentsname\docbooktolatexcontentsnametrue
\def\dbtolatex@contentslabel{%
 \label{\dbtolatex@contentsid}\hypertarget{\dbtolatex@contentsid}{\dbtolatex@@contentsname}%
 \global\docbooktolatexcontentsnamefalse}
\def\contentsname{\ifdocbooktolatexcontentsname\dbtolatex@contentslabel\else\dbtolatex@@contentsname\fi}
\let\save@@@mkboth\@mkboth
\let\@mkboth\@gobbletwo
\tableofcontents
\let\@mkboth\save@@@mkboth
\let\contentsname\latex@@contentsname
\Hy@writebookmark{}{\dbtolatex@@contentsname}{\dbtolatex@contentsid}{0}{toc}%
\makeatother
				</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text>\tableofcontents
</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:call-template name="latex.restoreparskip"/>
	</xsl:template><xsl:template match="lot" name="lot">
		<xsl:param name="prefer">
			<xsl:choose>
				<xsl:when test="@condition!=''">
					<xsl:value-of select="@condition"/>
				</xsl:when>
				<xsl:when test="@role!=''">
					<xsl:value-of select="@role"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="@label"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:param>
		<xsl:call-template name="latex.noparskip"/>
		<xsl:choose>
			<xsl:when test="$prefer='figures'">
				<xsl:text>\listoffigures
</xsl:text>
			</xsl:when>
			<xsl:when test="$prefer='tables'">
				<xsl:text>\listoftables
</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text>\listoffigures
</xsl:text>
				<xsl:text>\listoftables
</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:call-template name="latex.restoreparskip"/>
	</xsl:template><!--
	<xsl:template match="lotentry">
	</xsl:template>

	<xsl:template match="lotentry"/>
	<xsl:template match="tocpart|tocchap|tocfront|tocback|tocentry"/>
	<xsl:template match="toclevel1|toclevel2|toclevel3|toclevel4|toclevel5"/>
--><xsl:template name="generate.latex.pagestyle">
		<xsl:text>\pagestyle{</xsl:text>
		<xsl:choose>
			<xsl:when test="$latex.pagestyle!=''">
				<xsl:value-of select="$latex.pagestyle"/>
			</xsl:when>
			<xsl:when test="count(//book)&gt;0">
				<xsl:choose>
					<xsl:when test="$latex.use.fancyhdr=1"><xsl:text>fancy</xsl:text></xsl:when>
					<xsl:otherwise><xsl:text>plain</xsl:text></xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise><xsl:text>empty</xsl:text></xsl:otherwise>
		</xsl:choose>
		<xsl:text>}
</xsl:text>
	</xsl:template></xsl:stylesheet>
