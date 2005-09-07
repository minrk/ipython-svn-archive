<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: refentry.mod.xsl,v 1.7 2004/01/14 14:54:32 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="reference">
		<xsl:call-template name="map.begin"/>
		<xsl:call-template name="content-templates"/>
		<xsl:call-template name="map.end"/>
	</xsl:template><xsl:template match="refentry">
		<xsl:variable name="refmeta" select=".//refmeta"/>
		<xsl:variable name="refentrytitle" select="$refmeta//refentrytitle"/>
		<xsl:variable name="refnamediv" select=".//refnamediv"/>
		<xsl:variable name="refname" select="$refnamediv//refname"/>
		<xsl:variable name="title">
			<xsl:choose>
			<xsl:when test="$refentrytitle">
				<xsl:apply-templates select="$refentrytitle[1]"/>
			</xsl:when>
			<xsl:when test="$refname">
				<xsl:apply-templates select="$refname[1]"/>
				<xsl:apply-templates select="$refnamediv//refpurpose"/>
			</xsl:when>
			</xsl:choose>
		</xsl:variable>
		<xsl:call-template name="map.begin">
			<xsl:with-param name="string" select="$title"/>
		</xsl:call-template>
		<xsl:call-template name="content-templates"/>
		<xsl:call-template name="map.end">
			<xsl:with-param name="string" select="$title"/>
		</xsl:call-template>
	</xsl:template><xsl:template match="refmeta"/><xsl:template match="refentrytitle">
		<xsl:call-template name="inline.charseq"/>
	</xsl:template><!--
	<xsl:template match="refnamediv">
		<xsl:call-template name="block.object"/>
	</xsl:template>
	--><xsl:template match="manvolnum">
		<xsl:if test="$refentry.xref.manvolnum != 0">
			<xsl:text>(</xsl:text>
			<xsl:apply-templates/>
			<xsl:text>)</xsl:text>
		</xsl:if>
	</xsl:template><xsl:template match="refnamediv">
		<xsl:call-template name="block.object"/>
	</xsl:template><xsl:template match="refname">
		<xsl:if test="not (preceding-sibling::refname)">
			<xsl:text>
\section*{</xsl:text>
			<xsl:if test="$refentry.generate.name != 0">
			<xsl:call-template name="gentext.element.name"/>
			</xsl:if>
			<xsl:text>}
</xsl:text>
		</xsl:if>
		<xsl:apply-templates/>
		<xsl:if test="following-sibling::refname">
			<xsl:text>, </xsl:text>
		</xsl:if>
	</xsl:template><xsl:template match="refpurpose">
		<xsl:text> --- </xsl:text>
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="refdescriptor">
		<!-- todo: finish this -->
	</xsl:template><xsl:template match="refclass">
		<xsl:if test="@role!=''">
			<xsl:value-of select="@role"/>
			<xsl:text>: </xsl:text>
		</xsl:if>
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="refsynopsisdiv">
		<xsl:call-template name="label.id"/>
		<xsl:text>
\subsection*{Synopsis}
</xsl:text>
		<xsl:call-template name="content-templates"/>
	</xsl:template><xsl:template match="refsect1|refsect2|refsect3">
		<xsl:call-template name="map.begin"/>
		<xsl:call-template name="content-templates"/>
		<xsl:call-template name="map.end"/>
	</xsl:template></xsl:stylesheet>
