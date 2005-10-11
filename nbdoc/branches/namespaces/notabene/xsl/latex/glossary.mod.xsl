<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: glossary.mod.xsl,v 1.16 2004/01/26 08:58:10 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="glossary">
		<xsl:variable name="divs" select="glossdiv"/>
		<xsl:variable name="entries" select="glossentry"/>
		<xsl:variable name="preamble" select="node()[not(self::glossaryinfo or self::title or self::subtitle or self::titleabbrev or self::glossdiv or self::glossentry or self::bibliography)]"/>
		<xsl:call-template name="map.begin"/>
		<!--
		<xsl:if test="./subtitle"><xsl:apply-templates select="./subtitle" mode="component.title.mode"/> </xsl:if>
		-->
		<xsl:if test="$preamble"> <xsl:apply-templates select="$preamble"/> </xsl:if>
		<xsl:if test="$divs"> <xsl:apply-templates select="$divs"/> </xsl:if>
		<xsl:if test="$entries">
			<xsl:text>\noindent%
</xsl:text>
			<xsl:text>\begin{description}
</xsl:text>
			<xsl:apply-templates select="$entries"/>
			<xsl:text>\end{description}
</xsl:text>
		</xsl:if>
		<xsl:call-template name="map.end"/>
	</xsl:template><xsl:template match="glossdiv|glosslist">
		<xsl:call-template name="map.begin"/>
		<xsl:call-template name="content-templates"/>
		<xsl:call-template name="map.end"/>
	</xsl:template><!--
    <doc:template match="glossentry" xmlns="">
	<refpurpose> Glossary Entry XSL template / entry point  </refpurpose>
	<doc:description>
	    <para>T.B.D.</para>
	</doc:description>
	<itemizedlist>
	    <listitem><para>Apply Templates.</para></listitem>
	</itemizedlist>
	<formalpara><title>Remarks and Bugs</title>
	    <itemizedlist>
		<listitem><para>Explicit Templates for <literal>glossentry/glossterm</literal></para></listitem>
		<listitem><para>Explicit Templates for <literal>glossentry/acronym</literal></para></listitem>
		<listitem><para>Explicit Templates for <literal>glossentry/abbrev</literal></para></listitem>
		<listitem><para>Explicit Templates for <literal>glossentry/glossdef</literal></para></listitem>
		<listitem><para>Explicit Templates for <literal>glossentry/glosssee</literal></para></listitem>
		<listitem><para>Explicit Templates for <literal>glossentry/glossseealso</literal></para></listitem>
		<listitem><para>Template for glossentry/revhistory is EMPTY.</para></listitem>
	    </itemizedlist>
	</formalpara>
    </doc:template>
	--><xsl:template match="glossentry">
		<xsl:apply-templates/>
		<xsl:text>

</xsl:text>
	</xsl:template><xsl:template match="glossentry/glossterm">
		<xsl:text>\item[</xsl:text>
		<xsl:if test="../@id!=''">
			<xsl:text>\hypertarget{</xsl:text>
			<xsl:value-of select="../@id"/>
			<xsl:text>}</xsl:text>
		</xsl:if>
		<xsl:text>{</xsl:text>
		<xsl:apply-templates/>
		<xsl:text>}] </xsl:text>
	</xsl:template><xsl:template match="glossentry/acronym">
	<xsl:text> ( </xsl:text> <xsl:call-template name="inline.monoseq"/> <xsl:text> ) </xsl:text>
	</xsl:template><xsl:template match="glossentry/abbrev">
	<xsl:text> [ </xsl:text> <xsl:apply-templates/> <xsl:text> ] </xsl:text> 
	</xsl:template><xsl:template match="glossentry/revhistory"/><xsl:template match="glossentry/glossdef">
		<xsl:text>
</xsl:text>
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="glossseealso|glosssee">
		<xsl:variable name="otherterm" select="@otherterm"/>
		<xsl:variable name="targets" select="key('id',$otherterm)"/>
		<xsl:variable name="target" select="$targets[1]"/>
		<xsl:call-template name="gentext.element.name"/>
		<xsl:call-template name="gentext.space"/>
		<xsl:call-template name="gentext.startquote"/>
		<xsl:choose>
			<xsl:when test="$otherterm">
				<xsl:text>\hyperlink{</xsl:text><xsl:value-of select="$otherterm"/>
				<xsl:text>}{</xsl:text>
				<xsl:choose>
					<xsl:when test="$latex.otherterm.is.preferred=1">
						<xsl:apply-templates select="$target" mode="xref"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates/>
					</xsl:otherwise>
				</xsl:choose>
				<xsl:text>}</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates/>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:call-template name="gentext.endquote"/>
		<xsl:text>. </xsl:text>
	</xsl:template><xsl:template match="glossentry" mode="xref">
		<xsl:apply-templates select="./glossterm" mode="xref"/>
	</xsl:template><xsl:template match="glossterm" mode="xref">
		<xsl:apply-templates/>
	</xsl:template><xsl:template name="latex.preamble.essential.glossary">
		<xsl:if test="//glossary">
			<xsl:choose>
				<xsl:when test="/book or /part">
					<xsl:text>\newcommand{\dbglossary}[1]{\chapter*{#1}%
</xsl:text>
					<xsl:text>\markboth{\MakeUppercase{#1}}{\MakeUppercase{#1}}}%
</xsl:text>
					<xsl:text>\newcommand{\dbglossdiv}[1]{\section*{#1}}%
</xsl:text>
				</xsl:when>
				<xsl:otherwise>
					<xsl:text>\newcommand{\dbglossary}[1]{\section*{#1}}%
</xsl:text>
					<xsl:text>\newcommand{\dbglossdiv}[1]{\subsection*{#1}}%
</xsl:text>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:if>
	</xsl:template></xsl:stylesheet>
