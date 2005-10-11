<?xml version="1.0"?>
<!--############################################################################
|	$Id: param-common.mod.xsl,v 1.12 2004/01/26 13:25:17 j-devenish Exp $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:param name="admon.graphics.path">
		<xsl:choose>
			<xsl:when test="$latex.admonition.path!=''">
				<xsl:message>Warning: $latex.admonition.path is deprecated: use $admon.graphics.path instead</xsl:message>
				<xsl:value-of select="$latex.admonition.path"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text>figures</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:param><xsl:param name="latex.admonition.path"/><xsl:param name="tex.math.in.alt">
		<xsl:if test="$latex.alt.is.latex!=''">
			<xsl:message>Warning: $latex.alt.is.latex is deprecated: use $tex.math.in.alt instead</xsl:message>
			<xsl:if test="$latex.alt.is.latex=1">
				<xsl:text>latex</xsl:text>
			</xsl:if>
		</xsl:if>
	</xsl:param><xsl:param name="latex.alt.is.latex"/><xsl:param name="show.comments">
		<xsl:value-of select="$latex.is.draft"/>
	</xsl:param><xsl:param name="author.othername.in.middle" select="1"/><xsl:param name="biblioentry.item.separator">, </xsl:param><xsl:param name="toc.section.depth">4</xsl:param><xsl:param name="section.depth">4</xsl:param><xsl:param name="graphic.default.extension"/><xsl:param name="use.role.for.mediaobject">1</xsl:param><xsl:param name="preferred.mediaobject.role"/><xsl:param name="formal.title.placement">
		figure not_before
		example before
		equation not_before
		table before
		procedure before
	</xsl:param><xsl:param name="insert.xref.page.number">0</xsl:param><xsl:param name="ulink.show">1</xsl:param><xsl:param name="ulink.footnotes">0</xsl:param><xsl:param name="use.role.as.xrefstyle">0</xsl:param><xsl:variable name="default-classsynopsis-language">java</xsl:variable><xsl:param name="refentry.xref.manvolnum" select="1"/><xsl:variable name="funcsynopsis.style">kr</xsl:variable><xsl:variable name="funcsynopsis.decoration" select="1"/><xsl:variable name="function.parens">0</xsl:variable><xsl:param name="refentry.generate.name" select="1"/><xsl:param name="glossentry.show.acronym" select="'no'"/><xsl:variable name="section.autolabel" select="1"/><xsl:variable name="section.label.includes.component.label" select="0"/><xsl:variable name="chapter.autolabel" select="1"/><xsl:variable name="preface.autolabel" select="0"/><xsl:variable name="part.autolabel" select="1"/><xsl:variable name="qandadiv.autolabel" select="1"/><xsl:variable name="autotoc.label.separator" select="'. '"/><xsl:variable name="qanda.inherit.numeration" select="1"/><xsl:variable name="qanda.defaultlabel">number</xsl:variable><xsl:param name="punct.honorific" select="'.'"/><xsl:param name="stylesheet.result.type" select="'xhtml'"/><xsl:param name="use.svg" select="0"/><xsl:param name="formal.procedures" select="1"/><xsl:param name="xref.with.number.and.title" select="1"/><xsl:param name="xref.label-title.separator">: </xsl:param><xsl:param name="xref.label-page.separator"><xsl:text> </xsl:text></xsl:param><xsl:param name="xref.title-page.separator"><xsl:text> </xsl:text></xsl:param><xsl:template name="is.graphic.extension">
		<xsl:message terminate="yes">Logic error: is.graphic.extension is unsupported.</xsl:message>
	</xsl:template><xsl:template name="is.graphic.format">
		<xsl:message terminate="yes">Logic error: is.graphic.format is unsupported.</xsl:message>
	</xsl:template><xsl:template name="lookup.key">
		<xsl:message terminate="yes">Logic error: lookup.key is unsupported.</xsl:message>
	</xsl:template><xsl:variable name="check.idref">1</xsl:variable><xsl:param name="rootid" select="''"/><!--
    <xsl:variable name="link.mailto.url"></xsl:variable>
    <xsl:variable name="toc.list.type">dl</xsl:variable>
    --></xsl:stylesheet>
