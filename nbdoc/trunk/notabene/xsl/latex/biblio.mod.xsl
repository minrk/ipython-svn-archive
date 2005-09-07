<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: biblio.mod.xsl,v 1.21 2004/01/26 08:57:46 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

    <xsl:template name="latex.preamble.essential.biblio">
		<xsl:text>
			
\AtBeginDocument{\ifx\refname\@undefined\let\docbooktolatexbibname\bibname\def\docbooktolatexbibnamex{\bibname}\else\let\docbooktolatexbibname\refname\def\docbooktolatexbibnamex{\refname}\fi}
% Facilitate use of \cite with \label
\newcommand{\docbooktolatexbibaux}[2]{%
  \protected@write\@auxout{}{\string\global\string\@namedef{docbooktolatexcite@#1}{#2}}
}
% Provide support for bibliography `subsection' environments with titles
\newenvironment{docbooktolatexbibliography}[3]{
   \begingroup
   \let\save@@chapter\chapter
   \let\save@@section\section
   \let\save@@@mkboth\@mkboth
   \let\save@@bibname\bibname
   \let\save@@refname\refname
   \let\@mkboth\@gobbletwo
   \def\@tempa{#3}
   \def\@tempb{}
   \ifx\@tempa\@tempb
      \let\chapter\@gobbletwo
      \let\section\@gobbletwo
      \let\bibname\relax
   \else
      \let\chapter#2
      \let\section#2
      \let\bibname\@tempa
   \fi
   \let\refname\bibname
   \begin{thebibliography}{#1}
}{
   \end{thebibliography}
   \let\chapter\save@@chapter
   \let\section\save@@section
   \let\@mkboth\save@@@mkboth
   \let\bibname\save@@bibname
   \let\refname\save@@refname
   \endgroup
}

		</xsl:text>
	</xsl:template><xsl:template match="bibliography">
		<xsl:param name="makechapter" select="local-name(..)='book' or local-name(..)='part'"/>
		<xsl:variable name="keyword">
			<xsl:choose>
				<xsl:when test="$makechapter">
					<xsl:text>bibliography-chapter</xsl:text>
				</xsl:when>
				<xsl:otherwise>
					<xsl:text>bibliography-section</xsl:text>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="environment">
			<xsl:choose>
				<xsl:when test="$makechapter">thebibliography</xsl:when>
				<xsl:otherwise>docbooktolatexbibliography</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="title">
			<xsl:apply-templates select="title|subtitle"/>
		</xsl:variable>
		<!--
		<xsl:message>DB2LaTeX: Processing BIBLIOGRAPHY</xsl:message>
		-->
		<xsl:if test="$title!=''">
			<xsl:text>\let\oldbibname\bibname
</xsl:text>
			<xsl:text>\let\oldrefname\refname
</xsl:text>
			<xsl:text>\def\bibname{</xsl:text>
			<xsl:value-of select="$title"/>
			<xsl:text>}
</xsl:text>
			<xsl:text>\let\refname\bibname
</xsl:text>
		</xsl:if>
		<xsl:call-template name="map.begin">
			<xsl:with-param name="keyword" select="$keyword"/>
		</xsl:call-template>
		<xsl:choose>
			<xsl:when test="biblioentry or bibliodiv">
				<xsl:variable name="separatetitle" select="not(biblioentry or bibliodiv[1]/@title)"/>
				<xsl:message>DB2LaTeX: Bibliographic Output Mode :  <xsl:value-of select="$latex.biblio.output"/></xsl:message>
				<xsl:choose>
					<xsl:when test="$separatetitle and $makechapter">
						<xsl:text>\chapter*{\docbooktolatexbibnamex}\hypertarget{</xsl:text>
						<xsl:call-template name="generate.label.id"/>
						<xsl:text>}{}
</xsl:text>
					</xsl:when>
					<xsl:when test="$separatetitle and not($makechapter)">
						<xsl:text>\section*{\docbooktolatexbibnamex}\hypertarget{</xsl:text>
						<xsl:call-template name="generate.label.id"/>
						<xsl:text>}{}
</xsl:text>
					</xsl:when>
					<xsl:when test="biblioentry"><!-- implies not($separatetitle) -->
						<xsl:text>\begin{</xsl:text>
						<xsl:value-of select="$environment"/>
						<xsl:text>}{</xsl:text>
						<xsl:value-of select="$latex.bibwidelabel"/>
						<xsl:if test="$environment='docbooktolatexbibliography'">
							<xsl:text>}{\</xsl:text>
							<!-- TODO choose the correct nesting, rather than assuming something -->
							<xsl:choose>
								<xsl:when test="$makechapter">chapter</xsl:when>
								<xsl:otherwise>section</xsl:otherwise>
							</xsl:choose>
							<xsl:text>}{</xsl:text>
							<xsl:choose>
								<xsl:when test="$title!=''">
									<xsl:value-of select="$title"/>
								</xsl:when>
								<xsl:otherwise>
									<xsl:text>\docbooktolatexbibname</xsl:text>
								</xsl:otherwise>
							</xsl:choose>
						</xsl:if>
						<xsl:text>}\hypertarget{</xsl:text>
						<xsl:call-template name="generate.label.id"/>
						<xsl:text>}{}
</xsl:text>
						<xsl:choose>
							<xsl:when test="$latex.biblio.output ='cited'">
								<xsl:apply-templates select="biblioentry" mode="bibliography.cited">
									<xsl:sort select="./abbrev"/>
									<xsl:sort select="./@xreflabel"/>
									<xsl:sort select="./@id"/>
								</xsl:apply-templates>
							</xsl:when>
							<xsl:when test="$latex.biblio.output ='all'">
								<xsl:apply-templates select="biblioentry" mode="bibliography.all">
									<xsl:sort select="./abbrev"/>
									<xsl:sort select="./@xreflabel"/>
									<xsl:sort select="./@id"/>
								</xsl:apply-templates>
							</xsl:when>
							<xsl:otherwise>
								<xsl:apply-templates select="biblioentry">
									<xsl:sort select="./abbrev"/>
									<xsl:sort select="./@xreflabel"/>
									<xsl:sort select="./@id"/>
								</xsl:apply-templates>
							</xsl:otherwise>
						</xsl:choose>
						<!-- <xsl:apply-templates select="child::*[name(.)!='biblioentry']"/>  -->
						<xsl:text>
\end{</xsl:text>
						<xsl:value-of select="$environment"/>
						<xsl:text>}
</xsl:text>
					</xsl:when>
					<xsl:otherwise>
						<xsl:text>\hypertarget{</xsl:text>
						<xsl:call-template name="generate.label.id"/>
						<xsl:text>}{}
</xsl:text>
					</xsl:otherwise>
				</xsl:choose>
				<xsl:apply-templates select="bibliodiv"/>
			</xsl:when>
			<xsl:when test="child::*">
				<xsl:choose>
					<xsl:when test="$makechapter">
						<xsl:text>\chapter*</xsl:text>
					</xsl:when>
					<xsl:otherwise>
						<xsl:text>\section*</xsl:text>
					</xsl:otherwise>
				</xsl:choose>
				<xsl:text>{\docbooktolatexbibnamex}\hypertarget{</xsl:text>
				<xsl:call-template name="generate.label.id"/>
				<xsl:text>}{}
</xsl:text>
				<xsl:call-template name="content-templates"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text>% Assume that an empty &lt;bibliography&gt; means ``use BibTeX'' or similar.
</xsl:text>
				<xsl:text>\bibliography{</xsl:text><xsl:value-of select="$latex.bibfiles"/><xsl:text>}
</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:call-template name="map.end">
			<xsl:with-param name="keyword" select="$keyword"/>
		</xsl:call-template>
		<xsl:if test="$title!=''">
			<xsl:text>\let\bibname\oldbibname
</xsl:text>
			<xsl:text>\let\refname\oldrefname
</xsl:text>
		</xsl:if>
	</xsl:template><xsl:template match="processing-instruction('bibtex-bibliography')">
		<xsl:param name="makechapter" select="local-name(..)='book' or local-name(..)='part'"/>
		<xsl:param name="filename">
			<xsl:choose>
				<xsl:when test="normalize-space(.)!=''">
					<xsl:value-of select="."/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="$latex.bibfiles"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:param>
		<xsl:variable name="keyword">
			<xsl:choose>
				<xsl:when test="$makechapter">
					<xsl:text>bibliography-chapter</xsl:text>
				</xsl:when>
				<xsl:otherwise>
					<xsl:text>bibliography-section</xsl:text>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:call-template name="map.begin">
			<xsl:with-param name="keyword" select="$keyword"/>
		</xsl:call-template>
		<xsl:text>\bibliography{</xsl:text><xsl:value-of select="$filename"/><xsl:text>}
</xsl:text>
		<xsl:call-template name="map.end">
			<xsl:with-param name="keyword" select="$keyword"/>
		</xsl:call-template>
	</xsl:template><xsl:template match="bibliodiv">
		<xsl:param name="environment">
			<xsl:variable name="parent" select="local-name(..)"/>
			<xsl:choose>
				<xsl:when test="starts-with($parent,'sect')">docbooktolatexbibliography</xsl:when>
				<xsl:otherwise>thebibliography</xsl:otherwise>
			</xsl:choose>
		</xsl:param>
		<!--
		<xsl:message>DB2LaTeX: Processing BIBLIOGRAPHY - BIBLIODIV</xsl:message>
		-->
		<xsl:text>
\begin{docbooktolatexbibliography}{</xsl:text>
		<xsl:value-of select="$latex.bibwidelabel"/>
		<xsl:text>}{\</xsl:text>
		<!-- TODO choose the correct nesting, rather than assuming subsection -->
		<xsl:text>subsection</xsl:text>
		<xsl:text>}{</xsl:text>
		<xsl:apply-templates select="title|subtitle"/>
		<xsl:text>}\hypertarget{</xsl:text>
		<xsl:call-template name="generate.label.id"/>
		<xsl:text>}{}
</xsl:text>
		<xsl:choose>
			<xsl:when test="$latex.biblio.output ='cited'">
				<xsl:apply-templates select="biblioentry" mode="bibliography.cited">
					<xsl:sort select="./abbrev"/>
					<xsl:sort select="./@xreflabel"/>
					<xsl:sort select="./@id"/>
				</xsl:apply-templates>
			</xsl:when>
			<xsl:when test="$latex.biblio.output ='all'">
				<xsl:apply-templates select="biblioentry">
					<xsl:sort select="./abbrev"/>
					<xsl:sort select="./@xreflabel"/>
					<xsl:sort select="./@id"/>
				</xsl:apply-templates>
			</xsl:when>
		</xsl:choose>
		<xsl:text>
\end{docbooktolatexbibliography}
</xsl:text>
	</xsl:template><xsl:template match="biblioentry" mode="bibliography.cited">
		<xsl:param name="bibid" select="@id"/>
		<xsl:param name="ab" select="abbrev"/>
		<xsl:variable name="nx" select="//xref[@linkend=$bibid]"/>
		<xsl:variable name="nc" select="//citation[text()=$ab]"/>
		<xsl:if test="count($nx) &gt; 0 or count($nc) &gt; 0">
			<xsl:call-template name="biblioentry.output"/>
		</xsl:if>
	</xsl:template><xsl:template match="biblioentry" mode="bibliography.all">
		<xsl:call-template name="biblioentry.output"/>
	</xsl:template><xsl:template match="biblioentry">
		<xsl:call-template name="biblioentry.output"/>
	</xsl:template><xsl:template name="biblioentry.output">
		<xsl:variable name="biblioentry.label">
			<xsl:choose>
				<xsl:when test="@xreflabel">
					<xsl:value-of select="normalize-space(@xreflabel)"/> 
				</xsl:when>
				<xsl:when test="abbrev">
					<xsl:apply-templates select="abbrev" mode="bibliography.mode"/> 
				</xsl:when>
				<xsl:when test="@id">
					<xsl:value-of select="normalize-space(@id)"/> 
				</xsl:when>
				<xsl:otherwise>
					<!-- TODO is there any need for a warning? -->
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="biblioentry.id">
			<xsl:choose>
				<xsl:when test="abbrev">
					<xsl:apply-templates select="abbrev" mode="bibliography.mode"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:call-template name="generate.label.id"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:text>
</xsl:text>
		<xsl:call-template name="biblioentry.output.format">
			<xsl:with-param name="biblioentry.label" select="$biblioentry.label"/>
			<xsl:with-param name="biblioentry.id" select="$biblioentry.id"/>
		</xsl:call-template>
	</xsl:template><xsl:template name="biblioentry.output.format">
		<xsl:param name="biblioentry.label"/>
		<xsl:param name="biblioentry.id"/>
		<xsl:choose>
			<xsl:when test="$latex.biblioentry.style='ieee' or $latex.biblioentry.style='IEEE'">
				<xsl:text>% -------------- biblioentry 
</xsl:text>
				<xsl:text>\bibitem</xsl:text>
				<xsl:text>{</xsl:text>
				<xsl:value-of select="$biblioentry.id"/>
				<xsl:text>}\docbooktolatexbibaux{</xsl:text>
				<xsl:call-template name="generate.label.id"/>
				<xsl:text>}{</xsl:text>
				<xsl:value-of select="$biblioentry.id"/>
				<xsl:text>}
\hypertarget{</xsl:text>
				<xsl:call-template name="generate.label.id"/>
				<xsl:text>}
</xsl:text>
				<xsl:apply-templates select="author|authorgroup" mode="bibliography.mode"/>
				<xsl:value-of select="$biblioentry.item.separator"/>
				<xsl:text>\emph{</xsl:text> <xsl:apply-templates select="title" mode="bibliography.mode"/><xsl:text>}</xsl:text>
				<xsl:for-each select="child::copyright|child::publisher|child::pubdate|child::pagenums|child::isbn">
					<xsl:value-of select="$biblioentry.item.separator"/>
					<xsl:apply-templates select="." mode="bibliography.mode"/>
				</xsl:for-each>
				<xsl:text>. </xsl:text>
				<xsl:text>

</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text>% -------------- biblioentry 
</xsl:text>
				<xsl:choose>
					<xsl:when test="$biblioentry.label=''">
						<xsl:text>\bibitem</xsl:text> 
					</xsl:when>
					<xsl:otherwise>
						<xsl:text>\bibitem[{</xsl:text>
						<xsl:call-template name="normalize-scape">
							<xsl:with-param name="string" select="$biblioentry.label"/>
						</xsl:call-template>
						<xsl:text>}]</xsl:text>
					</xsl:otherwise>
				</xsl:choose>
				<xsl:text>{</xsl:text>
				<xsl:value-of select="$biblioentry.id"/>
				<xsl:text>}\docbooktolatexbibaux{</xsl:text>
				<xsl:call-template name="generate.label.id"/>
				<xsl:text>}{</xsl:text>
				<xsl:value-of select="$biblioentry.id"/>
				<xsl:text>}
\hypertarget{</xsl:text>
				<xsl:call-template name="generate.label.id"/>
				<xsl:text>}{\emph{</xsl:text> <xsl:apply-templates select="title" mode="bibliography.mode"/> <xsl:text>}}</xsl:text>
				<xsl:value-of select="$biblioentry.item.separator"/>
				<xsl:apply-templates select="author|authorgroup" mode="bibliography.mode"/>
				<xsl:for-each select="child::copyright|child::publisher|child::pubdate|child::pagenums|child::isbn|child::editor|child::releaseinfo">
					<xsl:value-of select="$biblioentry.item.separator"/>
					<xsl:apply-templates select="." mode="bibliography.mode"/>
				</xsl:for-each>
				<xsl:text>.</xsl:text>
				<xsl:text>

</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template name="biblioentry.output.format.ieee">
	</xsl:template><xsl:template match="abbrev" mode="bibliography.mode">
		<xsl:apply-templates mode="bibliography.mode"/>
    </xsl:template><!--
	<doc:template basename="abstract" match="abstract" mode="bibliography.mode" xmlns="">
		<refpurpose>Process <doc:db>abstract</doc:db> elements</refpurpose>
		<doc:description>
			<para>
				Currently, <doc:db basename="abstract">abstracts</doc:db> are deleted
				in <literal>bibliography.mode</literal>.
			</para>
		</doc:description>
		<doc:variables>
			&no_var;
		</doc:variables>
		<doc:notes>
			<para>Abstracts are suppressed in &DB2LaTeX; bibliographies.</para>
		</doc:notes>
	</doc:template>
	<xsl:template match="abstract" mode="bibliography.mode"/>
	--><xsl:template match="address" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="affiliation" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="authorblurb" mode="bibliography.mode"/><xsl:template match="artheader" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="artpagenums" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="author" mode="bibliography.mode">
		<xsl:apply-templates select="."/>
	</xsl:template><xsl:template match="authorgroup" mode="bibliography.mode">
		<xsl:apply-templates select="."/>
	</xsl:template><!-- basename="authorinitials" --><xsl:template match="authorinitials" mode="bibliography.mode">
		<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="bibliomisc" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="bibliomset" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="bibliomixed" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="biblioset" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="biblioset/title|biblioset/citetitle" mode="bibliography.mode">
	<xsl:variable name="relation" select="../@relation"/>
	<xsl:choose>
		<xsl:when test="$relation='article'">
		<xsl:call-template name="gentext.startquote"/>
		<xsl:apply-templates/>
		<xsl:call-template name="gentext.endquote"/>
		</xsl:when>
		<xsl:otherwise>
		<xsl:apply-templates/>
		</xsl:otherwise>
	</xsl:choose>
	</xsl:template><xsl:template match="bookbiblio" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="citetitle" mode="bibliography.mode">
	<I><xsl:apply-templates mode="bibliography.mode"/></I>
	</xsl:template><xsl:template match="collab" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="collabname" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="confgroup" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="confdates" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="conftitle" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="confnum" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="confsponsor" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="contractnum" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="contractsponsor" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="contrib" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="copyright" mode="bibliography.mode">
	<xsl:call-template name="gentext.element.name"/>
	<xsl:call-template name="gentext.space"/>
	<xsl:call-template name="dingbat">
		<xsl:with-param name="dingbat">copyright</xsl:with-param>
	</xsl:call-template>
	<xsl:call-template name="gentext.space"/>
	<xsl:apply-templates select="year" mode="bibliography.mode"/>
	<xsl:call-template name="gentext.space"/>
	<xsl:apply-templates select="holder" mode="bibliography.mode"/>
	</xsl:template><xsl:template match="year" mode="bibliography.mode">
	<xsl:apply-templates/><xsl:text>, </xsl:text>
	</xsl:template><xsl:template match="year[position()=last()]" mode="bibliography.mode">
	<xsl:apply-templates/>
	</xsl:template><xsl:template match="holder" mode="bibliography.mode">
	<xsl:apply-templates/>
	</xsl:template><xsl:template match="corpauthor" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="corpname" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="date" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="edition" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="editor" mode="bibliography.mode">
	<xsl:call-template name="person.name"/>
	</xsl:template><xsl:template match="firstname" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="honorific" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="indexterm" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="invpartnumber" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="isbn" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="issn" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="issuenum" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="jobtitle" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="lineage" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="orgname" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="orgdiv" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="othercredit" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="othername" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="pagenums" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="printhistory" mode="bibliography.mode">
	<!-- suppressed -->
	</xsl:template><xsl:template match="productname" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="productnumber" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="pubdate" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="publisher" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="publishername" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="pubsnumber" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="releaseinfo" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="revhistory" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="seriesinfo" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="seriesvolnums" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="shortaffil" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="subtitle" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="surname" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="title" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="titleabbrev" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="volumenum" mode="bibliography.mode">
	<xsl:apply-templates mode="bibliography.mode"/>
	</xsl:template><xsl:template match="*" mode="bibliography.mode">
	<xsl:apply-templates select="."/>
	</xsl:template></xsl:stylesheet>
